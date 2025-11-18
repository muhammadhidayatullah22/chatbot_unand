import os
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from openai import OpenAI
from nomic import embed
from docx import Document
import faiss
import numpy as np
import shutil
from typing import List, Optional, Dict
import traceback
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, create_tables, User
from chat_service import ChatService
from auth_service import AuthService
from admin_service import AdminService
import hashlib
from collections import OrderedDict

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv()

# OpenRouter / DeepSeek configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found. Please set it in environment or .env file.")

# Lazy OpenRouter client factory to avoid initializing during non-chat scripts
def get_openrouter_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

# Nomic API key (for embeddings)
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
if not NOMIC_API_KEY:
    raise ValueError("NOMIC_API_KEY not found. Please set it in environment or .env file.")

# Models (overridable via env)
# Default to Nomic embed text via OpenRouter
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text-v1.5")
GENERATIVE_MODEL = os.getenv("CHAT_MODEL", "tngtech/deepseek-r1t2-chimera:free")

# Optional fallbacks if the primary model is rate-limited or unavailable
# Comma-separated list, example:
# CHAT_MODEL_FALLBACKS="openai/gpt-4o-mini,qwen/qwen-2.5-7b-instruct:free,mistralai/mistral-7b-instruct:free"
# CHAT_MODEL_FALLBACKS = [
#     m.strip() for m in os.getenv(
#         "CHAT_MODEL_FALLBACKS",
#         "openai/gpt-4o-mini,qwen/qwen-2.5-7b-instruct:free,mistralai/mistral-7b-instruct:free"
#     ).split(",") if m.strip()
# ]
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "vector_db")
FAISS_INDEX_PATH = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")
DOC_CHUNKS_PATH = os.path.join(VECTOR_DB_DIR, "doc_chunks.json")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

faiss_index = None
doc_chunks = []

# --- In-Memory Cache for Query Responses (LRU Cache) ---
class QueryCache:
    """Simple LRU cache for query responses with TTL"""
    def __init__(self, max_size=100, ttl_minutes=60):
        self.cache: OrderedDict[str, Dict] = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _hash_query(self, query: str) -> str:
        """Create hash of normalized query for cache key"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict]:
        """Get cached response if exists and not expired"""
        key = self._hash_query(query)
        if key in self.cache:
            cached_data = self.cache[key]
            # Check if expired
            if datetime.now() - cached_data['timestamp'] < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                print(f"[CACHE] HIT for query: {query[:50]}...")
                return cached_data['response']
            else:
                # Expired, remove
                del self.cache[key]
                print(f"[CACHE] EXPIRED for query: {query[:50]}...")
        return None
    
    def set(self, query: str, response: Dict):
        """Cache a response"""
        key = self._hash_query(query)
        
        # Remove oldest if at max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
            print(f"[CACHE] Evicted oldest entry")
        
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
        print(f"[CACHE] STORED for query: {query[:50]}...")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        print(f"[CACHE] Cleared all entries")
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_minutes': self.ttl.total_seconds() / 60
        }

# Initialize cache (100 queries, 60 minutes TTL)
query_cache = QueryCache(max_size=100, ttl_minutes=60)

# --- Helper Functions for Document Processing ---
def load_faiss_index_and_chunks():
    """Loads FAISS index and document chunks if they exist."""
    global faiss_index, doc_chunks
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(DOC_CHUNKS_PATH):
        try:
            print("Loading FAISS index and document chunks...")
            faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            with open(DOC_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                doc_chunks = json.load(f)
            print("Loaded FAISS index and document chunks successfully.")
        except Exception as e:
            print(f"Error loading FAISS index or chunks: {e}. Will attempt to re-process.")
            faiss_index = None
            doc_chunks = []
    else:
        print("FAISS index or document chunks not found. Will run pre-processing.")
        faiss_index = None
        doc_chunks = []

def extract_text_from_docx(filepath):
    """Extracts text from a .docx file."""
    doc = Document(filepath)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return "\n".join(full_text)

def chunk_text(text, max_chars=1000, overlap=100):
    """Chunks text into smaller pieces with optional overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start += (max_chars - overlap)
    return chunks

def generate_embeddings_batch(texts: List[str], task_type="RETRIEVAL_DOCUMENT") -> List[List[float]]:
    """Generates embeddings for a list of texts using Nomic embeddings API."""
    embeddings: List[List[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        try:
            task = "search_document" if (task_type or "").upper().endswith("DOCUMENT") else "search_query"
            model_for_nomic = (EMBEDDING_MODEL or "nomic-embed-text-v1.5").split("/")[-1]
            out = embed.text(
                texts=batch_texts,
                model=model_for_nomic,
                task_type=task,
                dimensionality=768,
            )
            batch_embeddings = out.get("embeddings", [])
            if not batch_embeddings or len(batch_embeddings) != len(batch_texts):
                raise ValueError(f"Nomic returned {len(batch_embeddings)} embeddings for {len(batch_texts)} inputs")
            embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error generating embeddings for batch (index {i}): {e}")
            traceback.print_exc()
            # Fallback: zero vectors with Nomic dimension
            embeddings.extend([np.zeros(768).tolist()] * len(batch_texts))
    return embeddings

async def preprocess_documents_and_build_index():
    """Extract text, chunk, embed, and build/update FAISS index."""
    global faiss_index, doc_chunks
    print("Starting document pre-processing...")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

    all_chunks_with_metadata = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".docx") and not filename.startswith("~$"):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"Processing {filepath}...")
            try:
                text = extract_text_from_docx(filepath)
                chunks = chunk_text(text)
                # Add metadata for each chunk
                for chunk in chunks:
                    all_chunks_with_metadata.append({
                        "text": chunk,
                        "filename": filename,
                        "filepath": filepath
                    })
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue

    if not all_chunks_with_metadata:
        print("No text extracted from documents. Check your .docx files in backend/data.")
        faiss_index = None
        doc_chunks = []
        if os.path.exists(FAISS_INDEX_PATH):
            os.remove(FAISS_INDEX_PATH)
        if os.path.exists(DOC_CHUNKS_PATH):
            os.remove(DOC_CHUNKS_PATH)
        return

    print(f"Generated {len(all_chunks_with_metadata)} text chunks.")
    doc_chunks = all_chunks_with_metadata

    print("Generating embeddings for document chunks (this might take a while)...")
    # Extract only text for embedding generation
    chunk_texts = [chunk["text"] for chunk in doc_chunks]
    embeddings = generate_embeddings_batch(chunk_texts, task_type="RETRIEVAL_DOCUMENT")

    if not embeddings or len(embeddings) != len(doc_chunks):
        print("Failed to generate embeddings for all chunks. Aborting FAISS index creation.")
        faiss_index = None
        doc_chunks = []
        if os.path.exists(FAISS_INDEX_PATH):
            os.remove(FAISS_INDEX_PATH)
        if os.path.exists(DOC_CHUNKS_PATH):
            os.remove(DOC_CHUNKS_PATH)
        return

    embeddings_np = np.array(embeddings).astype('float32')
    dimension = embeddings_np.shape[1]

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings_np)

    # Save FAISS index and chunks
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    with open(DOC_CHUNKS_PATH, 'w', encoding='utf-8') as f:
        json.dump(doc_chunks, f, ensure_ascii=False, indent=2)

    print("Document pre-processing complete. FAISS index created/updated and saved.")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # INI YANG BARU: Inisialisasi klien dan simpan di app.state
    try:
        app.state.client = get_openrouter_client()
        print("OpenRouter client initialized and stored in app.state. Using model:", GENERATIVE_MODEL)
    except Exception as e:
        print(f"FATAL: Failed to initialize OpenRouter client: {e}")
    print("Database tables created/verified.")

    print("Loading existing FAISS index...")
    load_faiss_index_and_chunks()

    if faiss_index is None or not doc_chunks:
        print("No existing index found. Building new index...")
        await preprocess_documents_and_build_index()
        load_faiss_index_and_chunks()

    yield
    print("Application shutting down...")

app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

origins = [
    # Tambahkan domain publik frontend Anda dengan HTTPS
    "https://fe-chatbot.difunand.cloud",
    "https://www.fe-chatbot.difunand.cloud",
    # Tambahkan domain admin panel
    "https://admin.difunand.cloud",
    "https://www.admin.difunand.cloud",
    "https://admin.difunand.cloud",
    "https://www.admin.difunand.cloud",
    
    # Pertahankan localhost untuk testing internal
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:8080",
    "http://localhost:3005",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <-- Sekarang menggunakan daftar lengkap
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    auth_service = AuthService(db)
    user_id = auth_service.verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> str:
    """Get current authenticated admin"""
    admin_service = AdminService(db)

    admin_email = admin_service.verify_admin_token(credentials.credentials)
    if admin_email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin_email


async def get_current_user_optional(authorization: str = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        auth_service = AuthService(db)
        user_id = auth_service.verify_access_token(token)

        if user_id is None:
            return None

        return auth_service.get_user_by_id(user_id)
    except:
        return None


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []
    sources_count: int = 0
    summary: Optional[str] = None
    suggestions: Optional[str] = None
    is_greeting: bool = False

class SessionRequest(BaseModel):
    title: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str

class MessageResponse(BaseModel):
    id: int
    message_type: str
    content: str
    timestamp: str
    sources: Optional[List[str]] = None
    summary: Optional[str] = None
    suggestions: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str] = None


class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminAuthResponse(BaseModel):
    access_token: str
    token_type: str
    admin_email: str

 




@app.post("/auth/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db), req: Request = None):
    """Authenticate user with Google OAuth token"""
    auth_service = AuthService(db)
    admin_service = AdminService(db)

    try:
        user, access_token = auth_service.authenticate_user(request.token)

        # Log user login activity
        admin_service.log_user_activity(
            user_id=user.id,
            activity_type="login",
            request=req,
            details={"login_method": "google_oauth"}
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@app.post("/auth/logout")
async def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Logout user - sessions remain active for future access"""
    try:
        if current_user:
            return {
                "message": "Logout successful",
                "user_email": current_user.email
            }
        else:
            return {
                "message": "Logout successful",
                "user_email": None
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture
    )


@app.options("/chat")
async def options_chat():
    """Handle CORS preflight for /chat endpoint."""
    print("[CHAT] OPTIONS request received")
    return PlainTextResponse(status_code=200)

# (Letakkan ini di atas @app.post("/chat") )

async def stream_rag_response(
    query_text: str,
    unified_prompt: str,
    session_id: str,
    chat_service: ChatService,
    query_cache: QueryCache,
    chunks_by_file: Dict[str, List[str]] # <-- Tambahkan ini untuk parsing 'sources'
):
    """
    Generator function to stream response from OpenRouter,
    then save the full response to DB/Cache after completion.
    """
    full_response_text = ""
    start_time = datetime.now()
    
    try:
        # 1. Panggil API dengan stream=True
        print(f"[STREAM] Calling OpenRouter for session {session_id}...")
        stream = get_openrouter_client().chat.completions.create(
            model=GENERATIVE_MODEL,
            messages=[{"role": "user", "content": unified_prompt}],
            stream=True
        )
        
        # 2. Iterasi stream dan yield (kirim) chunks ke client
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content:
                full_response_text += content
                yield content
        
        time_after_stream = datetime.now()
        print(f"[TIMER] Stream completed in: {time_after_stream - start_time}")

        # 3. Setelah stream selesai, PARSE respons lengkap
        # (Logika ini disalin dari kode non-stream Anda)
        
        bot_response = full_response_text
        summary = None
        suggestions = None
        sources = [] # Default

        try:
            if "=== JAWABAN UTAMA ===" in full_response_text and "=== KESIMPULAN ===" in full_response_text:
                parts = full_response_text.split("=== JAWABAN UTAMA ===")
                if len(parts) > 1:
                    main_part = parts[1].split("=== KESIMPULAN ===")
                    bot_response = main_part[0].strip()
                    
                    if len(main_part) > 1:
                        rest = main_part[1]
                        
                        if "=== SARAN PRAKTIS ===" in rest:
                            summary_part = rest.split("=== SARAN PRAKTIS ===")
                            summary = summary_part[0].strip()
                            
                            if len(summary_part) > 1 and "=== SUMBER DOKUMEN ===" in summary_part[1]:
                                suggestions_part = summary_part[1].split("=== SUMBER DOKUMEN ===")
                                suggestions_text = suggestions_part[0].strip()
                                if suggestions_text and "tidak ada saran" not in suggestions_text.lower():
                                    suggestions = suggestions_text
                                
                                # EKSTRAKSI SUMBER YANG LEBIH BAIK
                                # Gunakan chunks_by_file yang kita punya
                                sources = [f"Dokumen: {filename}" for filename in chunks_by_file.keys()]

            # Jika parsing gagal, fallback ke teks penuh
            if not bot_response.strip():
                bot_response = full_response_text
                
        except Exception as parse_error:
            print(f"[STREAM] Could not parse structured response, using full text: {parse_error}")
            bot_response = full_response_text
            # Coba ambil sources dari context
            sources = [f"Dokumen: {filename}" for filename in chunks_by_file.keys()]


        # 4. Simpan ke Database (setelah stream selesai)
        print(f"[STREAM] Saving full response to DB for session {session_id}")
        chat_service.add_message(session_id, "bot", bot_response, sources, summary, suggestions)

        # 5. Simpan ke Cache (setelah stream selesai)
        print(f"[STREAM] Saving response to cache")
        cache_data = {
            'response': bot_response,
            'sources': sources,
            'summary': summary,
            'suggestions': suggestions
        }
        query_cache.set(query_text, cache_data)

    except Exception as e:
        print(f"Error during stream processing for query '{query_text}': {e}")
        traceback.print_exc()
        # Kirim pesan error sebagai bagian dari stream
        yield f"\n\n[ERROR] Terjadi kesalahan saat memproses jawaban: {str(e)}"
    
@app.post("/chat")
async def chat_with_rag(
    chat_request: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):

    print("[CHAT] ===== CHAT ENDPOINT CALLED =====")
    print(f"[CHAT] Request received at: {datetime.utcnow()}")
    print(f"[CHAT] Request type: {type(chat_request)}")
    print(f"[CHAT] Raw request data: {chat_request}")

    print(f"[CHAT] Received request: {chat_request.query}")
    print(f"[CHAT] Current user: {current_user.email if current_user else 'Guest'}")
    print(f"[CHAT] FAISS index status: {faiss_index is not None}")
    print(f"[CHAT] Doc chunks count: {len(doc_chunks) if doc_chunks else 0}")

    if faiss_index is None or not doc_chunks:
        # Memberikan pesan yang lebih informatif jika indeks belum siap
        print(f"[CHAT] Error: System not ready - FAISS index: {faiss_index is not None}, Doc chunks: {len(doc_chunks) if doc_chunks else 0}")
        raise HTTPException(status_code=500, detail="Sistem belum siap. Indeks dokumen sedang dibuat atau belum ada dokumen yang diunggah. Mohon tunggu atau unggah dokumen.")

    query_text = chat_request.query
    chat_service = ChatService(db)

    # Handle session
    session_id = chat_request.session_id
    is_new_session = False
    if not session_id:
        # Create new session with title from first message
        title = chat_service.generate_session_title(query_text)
        user_id = current_user.id if current_user else None
        print(f"[CHAT] Creating new session for user_id: {user_id}, title: {title}")
        session_id = chat_service.create_session(title, user_id)
        print(f"[CHAT] Created session with ID: {session_id}")
        is_new_session = True

    # Save user message
    chat_service.add_message(session_id, "user", query_text)

    # Check if this is a greeting message (new session and simple greeting) or test question
    greeting_keywords = ["halo", "hai", "hello", "hi", "selamat", "assalamualaikum", "permisi"]
    test_keywords = ["tes", "test"]
    is_greeting = is_new_session and any(keyword in query_text.lower() for keyword in greeting_keywords)
    is_test_question = query_text.lower().strip() in test_keywords

    # If it's a greeting or test question, return appropriate response without RAG
    if is_greeting or is_test_question:
        if is_test_question:
            response_text = "Halo! Saya adalah chatbot Universitas Andalas yang siap membantu Anda dengan informasi seputar peraturan akademik dan kebijakan universitas. Anda dapat bertanya tentang berbagai topik seperti syarat kelulusan, sanksi akademik, peraturan studi, dan informasi akademik lainnya. Silakan ajukan pertanyaan Anda!"
        else:
            response_text = "Halo! Saya adalah Chatbot UNAND. Saya siap membantu Anda dengan pertanyaan seputar peraturan kampus dan pemerintah. Silakan ajukan pertanyaan Anda!"

        # Save bot response without sources for greeting/test
        chat_service.add_message(session_id, "bot", response_text, [], None, None)

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=[],
            sources_count=0,
            summary=None,
            suggestions=None,
            is_greeting=True
        )

    # Check cache before expensive RAG processing
    cached_response = query_cache.get(query_text)
    if cached_response:
        # Save cached response to message history
        chat_service.add_message(
            session_id, "bot", 
            cached_response['response'], 
            cached_response.get('sources', []), 
            cached_response.get('summary'), 
            cached_response.get('suggestions')
        )
        
        return ChatResponse(
            response=cached_response['response'],
            session_id=session_id,
            sources=cached_response.get('sources', []),
            sources_count=len(cached_response.get('sources', [])),
            summary=cached_response.get('summary'),
            suggestions=cached_response.get('suggestions'),
            is_greeting=False
        )

    try:
        start_time = datetime.now()
        print(f"[TIMER] Start processing time: {start_time}")
        # 1. Generate embedding for the query via Nomic
        model_for_nomic = (EMBEDDING_MODEL or "nomic-embed-text-v1.5").split("/")[-1]
        time_before_nomic = datetime.now()
        print(f"[TIMER] Time before Nomic API: {time_before_nomic - start_time}")
        out = embed.text(
            texts=[query_text],
            model=model_for_nomic,
            task_type="search_query",
            dimensionality=768,
        )
        time_after_nomic = datetime.now()
        print(f"[TIMER] Time after Nomic API: {time_after_nomic - time_before_nomic}")
        vec = out.get("embeddings", [None])[0]
        if vec is None:
            raise ValueError(f"Unexpected response format from Nomic embed: {out}")

        query_vector = np.array(vec).astype('float32')
        index_dim = faiss_index.d
        if query_vector.shape[0] != index_dim:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Dimensi embedding query ({query_vector.shape[0]}) tidak cocok dengan index ({index_dim}). "
                    f"Mohon rebuild index menggunakan EMBEDDING_MODEL yang sama dengan saat query: {EMBEDDING_MODEL}."
                ),
            )

        query_embedding = query_vector.reshape(1, -1)

        # 2. Search FAISS index for relevant chunks
        k = 8 # Optimized: reduced from 15 to 8 for faster processing
        time_before_faiss = datetime.now()
        print(f"[TIMER] Time before FAISS search: {time_before_faiss - time_after_nomic}")
        distances, indices = faiss_index.search(query_embedding, k)
        time_after_faiss = datetime.now()
        print(f"[TIMER] Time after FAISS search: {time_after_faiss - time_before_faiss}")
        # Filter out invalid indices and apply score threshold
        # Score threshold: 0.7 (optimized for better relevance)
        score_threshold = 0.7
        relevant_chunks_with_metadata = []

        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if 0 <= idx < len(doc_chunks):
                # Convert distance to similarity score (FAISS uses L2 distance, lower is better)
                # For L2 distance, we can use 1/(1+distance) as similarity
                similarity_score = 1.0 / (1.0 + distance)

                if similarity_score >= score_threshold:
                    chunk_data = doc_chunks[idx].copy()
                    chunk_data['similarity_score'] = similarity_score
                    relevant_chunks_with_metadata.append(chunk_data)

        # If no chunks meet threshold, take top 5 chunks anyway (fallback)
        if not relevant_chunks_with_metadata:
            relevant_chunks_with_metadata = [doc_chunks[i] for i in indices[0][:5] if 0 <= i < len(doc_chunks)]
        else:
            # Limit to top 5 chunks for context (optimized from 8)
            relevant_chunks_with_metadata = relevant_chunks_with_metadata[:5]

        # Extract text for processing and group by filename
        chunks_by_file = {}
        for chunk_data in relevant_chunks_with_metadata:
            filename = chunk_data["filename"]
            if filename not in chunks_by_file:
                chunks_by_file[filename] = []
            chunks_by_file[filename].append(chunk_data["text"])

        # Debug info with optimized retrieval metrics
        print(f"[OPTIMIZATION] Query: {query_text}")
        print(f"[OPTIMIZATION] Config: k={k}, threshold={score_threshold}, max_chunks=5")
        print(f"[OPTIMIZATION] Found {len(relevant_chunks_with_metadata)} chunks from {len(chunks_by_file)} files")

        # Show similarity scores for debugging
        for i, chunk_data in enumerate(relevant_chunks_with_metadata[:5]):  # Show top 5
            score = chunk_data.get('similarity_score', 'N/A')
            print(f"Chunk {i+1}: similarity={score:.3f}" if score != 'N/A' else f"Chunk {i+1}: similarity=N/A")

        for filename, chunks in chunks_by_file.items():
            print(f"File {filename}: {len(chunks)} chunks")

        if not relevant_chunks_with_metadata:
            return {"response": "Maaf, saya tidak menemukan informasi relevan dalam dokumen peraturan yang ada untuk pertanyaan Anda."}

        # 3. Construct prompt for Gemini (RAG approach) - OPTIMIZED UNIFIED PROMPT
        # Combine all chunks for context
        all_relevant_texts = [chunk_data["text"] for chunk_data in relevant_chunks_with_metadata]
        context = "\n\n".join(all_relevant_texts)

        # Prepare document sources info for structured output
        sources_info = []
        for filename, chunks in chunks_by_file.items():
            sources_info.append(f"- {filename}")
        sources_list_text = "\n".join(sources_info)

        # Detect question type for specialized formatting
        query_lower = query_text.lower()
        is_dropout_question = any(keyword in query_lower for keyword in ['drop out', 'dropout', 'sanksi', 'pemutusan', 'dikeluarkan'])

        # 4. UNIFIED PROMPT - Single API call for complete response (Optimized: 11 calls → 1 call)
        time_before_prompt = datetime.now()
        print(f"[TIMER] Time before prompt: {time_before_prompt - time_after_faiss}")
        if is_dropout_question:
            unified_prompt = f"""Anda adalah asisten AI untuk Universitas Andalas yang ahli dalam peraturan akademik.

DOKUMEN PERATURAN YANG TERSEDIA:
{sources_list_text}

KONTEN DOKUMEN:
{context}

PERTANYAAN: {query_text}

INSTRUKSI OUTPUT - Berikan respons LENGKAP dalam format SANGAT TERSTRUKTUR berikut:

=== JAWABAN UTAMA ===
[WAJIB ikuti struktur ini untuk pertanyaan tentang drop out/sanksi:

Berdasarkan dokumen [nama peraturan lengkap], persyaratan drop out/pemutusan studi di Universitas Andalas diatur berdasarkan jenjang program pendidikan sebagai berikut:

**Persyaratan Drop Out per Jenjang Program:**

1. **Program Sarjana (S1):**
   Mahasiswa dinyatakan drop out apabila:
   • [Syarat pertama dengan detail lengkap]
   • [Syarat kedua dengan detail lengkap]
   • [Syarat ketiga jika ada]

2. **Program Diploma III (D3):**
   Drop out diberlakukan apabila:
   • [Syarat pertama dengan detail lengkap]
   • [Syarat kedua dengan detail lengkap]
   • [Syarat ketiga jika ada]

3. **Program Magister (S2):**
   (Jika ada dalam dokumen, jelaskan dengan format yang sama)

4. **Program Doktor (S3):**
   (Jika ada dalam dokumen, jelaskan dengan format yang sama)

**Referensi:** Pasal [X], [Nama Peraturan Lengkap]

PENTING:
- Gunakan spasi untuk memisahkan setiap section
- Bold untuk judul program
- Bullet points untuk setiap syarat
- Detail yang lengkap dan spesifik (semester, SKS, IPK, dll)]

=== KESIMPULAN ===
[Ringkasan 2-3 kalimat yang mencakup semua jenjang program yang dijelaskan.]

=== SARAN PRAKTIS ===
[Berikan 3 saran untuk mahasiswa agar terhindar dari drop out:
1. [Saran pertama yang actionable]
2. [Saran kedua yang konkret]
3. [Saran ketiga yang praktis]]

=== SUMBER DOKUMEN ===
[Untuk setiap dokumen:

Dokumen: [nama file lengkap]
Informasi: [Penjelasan detail tentang bab/pasal yang mengatur drop out dalam dokumen ini]

(Ulangi untuk tiap dokumen)]

KUALITAS: Pastikan jawaban sangat terstruktur, rapi, dan mudah dipahami mahasiswa."""

        else:
            unified_prompt = f"""Anda adalah asisten AI untuk Universitas Andalas yang ahli dalam peraturan akademik.

DOKUMEN PERATURAN YANG TERSEDIA:
{sources_list_text}

KONTEN DOKUMEN:
{context}

PERTANYAAN: {query_text}

INSTRUKSI OUTPUT - Berikan respons LENGKAP dalam format SANGAT TERSTRUKTUR berikut:

=== JAWABAN UTAMA ===
[WAJIB ikuti struktur ini:

1. Paragraf pembuka (2-3 kalimat):
   - Mulai dengan "Berdasarkan dokumen [nama peraturan], ..."
   - Jelaskan konteks umum dari pertanyaan
   
2. Isi jawaban dengan format yang SANGAT RAPI:
   - Gunakan numbering (1. 2. 3.) untuk poin utama
   - Gunakan bullet points (•) untuk sub-poin di bawah setiap nomor
   - Tambahkan indentasi yang jelas untuk hierarki informasi
   - Gunakan **bold** untuk judul/kategori penting
   - Pisahkan setiap poin dengan spasi kosong untuk readability
   
3. Format contoh yang WAJIB diikuti:
   
   **[Kategori/Topik Utama]:**
   
   1. **[Sub-kategori pertama]:**
      • Poin detail pertama
      • Poin detail kedua
      • Poin detail ketiga
   
   2. **[Sub-kategori kedua]:**
      • Poin detail pertama
      • Poin detail kedua
   
4. Referensi:
   - Selalu cantumkan sumber di akhir setiap section penting
   - Format: "Referensi: Pasal [X], [Nama Peraturan]"
   
PENTING: 
- Gunakan spasi dan line break untuk memisahkan section
- Jangan terlalu padat, buat breathable
- Konsisten dengan formatting
- Integrasikan SEMUA dokumen yang relevan]

=== KESIMPULAN ===
[Tulis 2-3 kalimat ringkasan yang padat dan jelas, mencakup poin-poin utama dari jawaban di atas.]

=== SARAN PRAKTIS ===
[Berikan 3 saran konkret dalam format numbered list:
1. [Saran pertama yang actionable]
2. [Saran kedua yang spesifik]
3. [Saran ketiga yang relevan]

Jika benar-benar tidak ada saran yang relevan, tulis "Tidak ada saran khusus untuk pertanyaan ini."]

=== SUMBER DOKUMEN ===
[Untuk setiap dokumen yang digunakan:

Dokumen: [nama file lengkap]
Informasi: [Penjelasan 2-3 kalimat tentang apa yang dijelaskan dokumen ini terkait pertanyaan, termasuk pasal/bab yang spesifik]

(Ulangi untuk setiap dokumen relevan)]

KUALITAS OUTPUT: Pastikan jawaban sangat terstruktur, mudah dibaca, dan profesional seperti dokumen resmi universitas."""

        # Single unified API call using OpenRouter Chat Completions with retry + fallbacks
        print(f"[OPTIMIZATION] Using unified prompt - single API call via OpenRouter Chat Completions")

        def call_with_retries(model_name: str):
            max_attempts = 3
            backoff_seconds = 0.6
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"[OPENROUTER] Attempt {attempt}/{max_attempts} using model: {model_name}")
                    return get_openrouter_client().chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": unified_prompt}],
                    )
                except Exception as err:
                    last_error = err
                    err_text = str(err)
                    is_rate_limited = (
                        "429" in err_text
                        or "rate limit" in err_text.lower()
                        or "rate-limited" in err_text.lower()
                    )
                    if attempt < max_attempts and is_rate_limited:
                        print(f"[OPENROUTER] Rate limited on {model_name}. Backing off {backoff_seconds:.1f}s then retry...")
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                        continue
                    print(f"[OPENROUTER] Error on {model_name}: {err}")
                    break
            raise last_error if last_error else RuntimeError("Unknown error calling OpenRouter")

        # Try only the primary model with retries (no fallbacks)
        try:
            completion = call_with_retries(GENERATIVE_MODEL)
            print(f"[OPENROUTER] Success with model: {GENERATIVE_MODEL}")
        except Exception:
            # Explicitly raise with friendly message
            raise HTTPException(
                status_code=500,
                detail=(
                    "Terjadi kesalahan saat menghubungi penyedia model (kemungkinan rate limit). "
                    "Mohon coba lagi beberapa saat atau ganti CHAT_MODEL ke model lain."
                ),
            )
        time_after_prompt = datetime.now()
        print(f"[TIMER] Time after prompt: {time_after_prompt - time_before_prompt}")
        response_text = (completion.choices[0].message.content if completion and completion.choices else None)

        if not response_text:
            bot_response = "Maaf, saya tidak dapat menghasilkan jawaban yang relevan saat ini."
            summary = None
            suggestions = None
            sources = []
        else:
            
            # Parse structured response
            # Extract main answer (between === JAWABAN UTAMA === and === KESIMPULAN ===)
            bot_response = response_text
            summary = None
            suggestions = None
            sources = []
            
            try:
                # Try to parse structured sections
                if "=== JAWABAN UTAMA ===" in response_text and "=== KESIMPULAN ===" in response_text:
                    parts = response_text.split("=== JAWABAN UTAMA ===")
                    if len(parts) > 1:
                        main_part = parts[1].split("=== KESIMPULAN ===")
                        bot_response = main_part[0].strip()
                        
                        if len(main_part) > 1:
                            rest = main_part[1]
                            
                            # Extract summary
                            if "=== SARAN PRAKTIS ===" in rest:
                                summary_part = rest.split("=== SARAN PRAKTIS ===")
                                summary = summary_part[0].strip()
                                
                                # Extract suggestions
                                if len(summary_part) > 1 and "=== SUMBER DOKUMEN ===" in summary_part[1]:
                                    suggestions_part = summary_part[1].split("=== SUMBER DOKUMEN ===")
                                    suggestions_text = suggestions_part[0].strip()
                                    if suggestions_text and "tidak ada saran" not in suggestions_text.lower():
                                        suggestions = suggestions_text
                                    
                                    # Extract sources
                                    if len(suggestions_part) > 1:
                                        sources_text = suggestions_part[1].strip()
                                        if sources_text and len(sources_text) > 20:
                                            # Split by "Dokumen:" to get individual sources
                                            source_items = [s.strip() for s in sources_text.split("Dokumen:") if s.strip()]
                                            sources = [f"Dokumen: {s}" for s in source_items]
                
                # If parsing failed, use the whole response as answer
                if not bot_response or bot_response == response_text:
                    bot_response = response_text
                    # Try simple extraction for summary at least
                    if "kesimpulan:" in response_text.lower():
                        parts = response_text.lower().split("kesimpulan:")
                        if len(parts) > 1:
                            summary_candidate = parts[1].split("\n\n")[0].strip()
                            if len(summary_candidate) < 500:  # Reasonable summary length
                                summary = summary_candidate
                                
            except Exception as parse_error:
                print(f"[OPTIMIZATION] Could not parse structured response, using full text: {parse_error}")
                bot_response = response_text

        # Save bot response
        chat_service.add_message(session_id, "bot", bot_response, sources, summary, suggestions)

        # Cache the response for future similar queries
        cache_data = {
            'response': bot_response,
            'sources': sources,
            'summary': summary,
            'suggestions': suggestions
        }
        query_cache.set(query_text, cache_data)

        return ChatResponse(
            response=bot_response,
            session_id=session_id,
            sources=sources,
            sources_count=len(sources),
            summary=summary,
            suggestions=suggestions,
            is_greeting=False
        )

    except Exception as e:
        print(f"Error during chat processing for query '{query_text}': {e}")
        # Log the full traceback for debugging in development
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal saat memproses pertanyaan Anda: {e}. Mohon coba lagi.")

# Session management endpoints
@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Create a new chat session"""
    chat_service = ChatService(db)
    user_id = current_user.id if current_user else None
    session_id = chat_service.create_session(request.title or "New Chat", user_id)
    session = chat_service.get_session(session_id)

    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat()
    )

@app.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Get all chat sessions for current user"""
    print(f"[SESSIONS] Get sessions called")
    print(f"[SESSIONS] Current user: {current_user.email if current_user else 'Guest'}")

    chat_service = ChatService(db)
    if current_user:
        print(f"[SESSIONS] Loading sessions for user ID: {current_user.id}")
        sessions = chat_service.get_all_sessions(current_user.id)
        print(f"[SESSIONS] Found {len(sessions)} sessions for user {current_user.email}")
    else:
        # Return empty list for guest users
        print(f"[SESSIONS] Guest user - returning empty sessions")
        sessions = []

    return [
        SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
        for session in sessions
    ]

@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Get all messages for a session"""
    chat_service = ChatService(db)

    # Verify session belongs to current user
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If user is logged in, check if session belongs to them
    if current_user and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    # If user is not logged in and session has a user_id, deny access
    if not current_user and session.user_id is not None:
        raise HTTPException(status_code=401, detail="Authentication required")

    messages = chat_service.get_messages(session_id)

    return [
        MessageResponse(
            id=msg.id,
            message_type=msg.message_type,
            content=msg.content,
            timestamp=msg.timestamp.isoformat(),
            sources=json.loads(msg.sources) if msg.sources else None,
            summary=msg.summary,
            suggestions=msg.suggestions
        )
        for msg in messages
    ]

@app.put("/sessions/{session_id}")
async def update_session(session_id: str, request: SessionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Update session title"""
    chat_service = ChatService(db)

    # Verify session belongs to current user
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If user is logged in, check if session belongs to them
    if current_user and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    # If user is not logged in and session has a user_id, deny access
    if not current_user and session.user_id is not None:
        raise HTTPException(status_code=401, detail="Authentication required")

    success = chat_service.update_session_title(session_id, request.title)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session updated successfully"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_optional)):
    """Delete a session"""
    chat_service = ChatService(db)

    # Verify session belongs to current user
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If user is logged in, check if session belongs to them
    if current_user and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    # If user is not logged in and session has a user_id, deny access
    if not current_user and session.user_id is not None:
        raise HTTPException(status_code=401, detail="Authentication required")

    success = chat_service.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted successfully"}

# Handle CORS preflight for /upload-document explicitly


# Admin endpoints
@app.post("/admin/login", response_model=AdminAuthResponse)
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin login with email and password"""
    admin_service = AdminService(db)

    if not admin_service.authenticate_admin(request.email, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )

    access_token = admin_service.create_admin_token(request.email)

    return AdminAuthResponse(
        access_token=access_token,
        token_type="bearer",
        admin_email=request.email
    )

@app.get("/admin/dashboard")
async def get_admin_dashboard(admin_email: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Get admin dashboard data"""
    admin_service = AdminService(db)

    user_stats = admin_service.get_user_stats()
    user_activities = admin_service.get_user_activities(limit=50)
    all_users = admin_service.get_all_users()

    return {
        "user_stats": user_stats,
        "recent_activities": user_activities,
        "all_users": all_users
    }

@app.get("/admin/users/activities")
async def get_user_activities(
    limit: int = 100,
    admin_email: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user activities log"""
    admin_service = AdminService(db)
    return admin_service.get_user_activities(limit)

@app.get("/admin/users/stats")
async def get_user_stats(admin_email: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Get user statistics"""
    admin_service = AdminService(db)
    return admin_service.get_user_stats()

@app.get("/admin/files")
async def get_knowledge_files(admin_email: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Get all knowledge base files"""
    admin_service = AdminService(db)
    files = admin_service.get_knowledge_files()

    # Enrich with processed chunk counts using current doc_chunks (or file fallback)
    try:
        chunks_source = doc_chunks
        if (not chunks_source) and os.path.exists(DOC_CHUNKS_PATH):
            with open(DOC_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                chunks_source = json.load(f)

        counts_by_filename: Dict[str, int] = {}
        for ch in chunks_source or []:
            filename = ch.get('filename')
            if filename:
                counts_by_filename[filename] = counts_by_filename.get(filename, 0) + 1

        # files is expected to be a list of dict-like objects
        enriched = []
        for item in files:
            try:
                filename = item.get('filename') if isinstance(item, dict) else getattr(item, 'filename', None)
                processed = counts_by_filename.get(filename, 0)
                if isinstance(item, dict):
                    item['processed_chunks'] = processed
                    enriched.append(item)
                else:
                    # Convert to dict conservatively if it's an ORM model
                    enriched.append({
                        **{k: getattr(item, k) for k in dir(item) if not k.startswith('_') and not callable(getattr(item, k))},
                        'processed_chunks': processed,
                    })
            except Exception:
                enriched.append(item)

        return enriched
    except Exception as e:
        print(f"Failed to enrich knowledge files with chunk counts: {e}")
        return files

@app.get("/admin/users")
async def get_all_users(admin_email: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Get all users with their statistics"""
    admin_service = AdminService(db)
    return admin_service.get_all_users()

@app.post("/admin/files/sync")
async def sync_files_from_data_dir(
    admin_email: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Scan backend/data for .docx files and ensure they are recorded in database.

    This helps when files were copied manually to the data directory without using the upload API.
    """
    admin_service = AdminService(db)

    # Existing records by filename
    existing = admin_service.get_knowledge_files()
    existing_filenames = set([f["filename"] for f in existing])

    data_dir = DATA_DIR
    os.makedirs(data_dir, exist_ok=True)

    created = []
    for filename in os.listdir(data_dir):
        if not filename.lower().endswith(".docx") or filename.startswith("~$"):
            continue
        if filename in existing_filenames:
            continue

        file_path = os.path.join(data_dir, filename)
        try:
            file_size = os.path.getsize(file_path)
            knowledge_file = admin_service.add_knowledge_file(
                filename=filename,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                uploaded_by=admin_email,
            )
            created.append({"id": knowledge_file.id, "filename": filename})
        except Exception as e:
            print(f"Sync error for {filename}: {e}")

    # Rebuild index if we added anything
    knowledge_base_updated = False
    if created:
        try:
            await preprocess_documents_and_build_index()
            load_faiss_index_and_chunks()
            knowledge_base_updated = True
        except Exception as e:
            print(f"Error rebuilding knowledge base after sync: {e}")

    return {
        "synced": len(created),
        "created": created,
        "knowledge_base_updated": knowledge_base_updated,
    }

@app.post("/admin/files/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    admin_email: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload new knowledge base file"""
    admin_service = AdminService(db)

    # Validate file type
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are supported"
        )

    try:
        # Save file to data directory
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)

        file_path = os.path.join(data_dir, file.filename)

        # Check if file already exists
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} already exists"
            )

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Add to database
        knowledge_file = admin_service.add_knowledge_file(
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            uploaded_by=admin_email
        )

        # Trigger reindexing immediately after upload
        print("File uploaded successfully. Rebuilding knowledge base...")
        try:
            await preprocess_documents_and_build_index()
            load_faiss_index_and_chunks()
            print("Knowledge base rebuilt successfully after file upload.")

            return {
                "message": "File uploaded successfully and knowledge base updated",
                "file_id": knowledge_file.id,
                "filename": knowledge_file.filename,
                "file_size": knowledge_file.file_size,
                "knowledge_base_updated": True
            }
        except Exception as rebuild_error:
            print(f"Error rebuilding knowledge base after upload: {rebuild_error}")
            return {
                "message": "File uploaded successfully but knowledge base update failed",
                "file_id": knowledge_file.id,
                "filename": knowledge_file.filename,
                "file_size": knowledge_file.file_size,
                "knowledge_base_updated": False,
                "error": str(rebuild_error)
            }

    except Exception as e:
        # Clean up file if database operation failed
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@app.delete("/admin/files/{file_id}")
async def delete_knowledge_file(
    file_id: int,
    admin_email: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete knowledge base file and rebuild index"""
    admin_service = AdminService(db)

    if admin_service.delete_knowledge_file(file_id):
        # Rebuild knowledge base after file deletion
        print("File deleted successfully. Rebuilding knowledge base...")
        try:
            await preprocess_documents_and_build_index()
            load_faiss_index_and_chunks()
            print("Knowledge base rebuilt successfully after file deletion.")
            return {
                "message": "File deleted successfully and knowledge base updated",
                "knowledge_base_updated": True
            }
        except Exception as e:
            print(f"Error rebuilding knowledge base after deletion: {e}")
            return {
                "message": "File deleted successfully but knowledge base update failed",
                "knowledge_base_updated": False,
                "error": str(e)
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    stats = query_cache.stats()
    return {
        "cache_size": stats['size'],
        "cache_max_size": stats['max_size'],
        "cache_ttl_minutes": stats['ttl_minutes'],
        "cache_hit_rate": f"{stats['size']}/{stats['max_size']}"
    }

@app.post("/cache/clear")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """Clear all cache (requires authentication)"""
    query_cache.clear()
    return {"message": "Cache cleared successfully"}

@app.get("/health")
async def health_check():
    """Endpoint to check if the server is running and index is loaded."""
    status = "OK" if faiss_index is not None and len(doc_chunks) > 0 else "Indexing_In_Progress_or_Failed"
    chunk_count_val = len(doc_chunks) if doc_chunks else 0
    cache_stats = query_cache.stats()
    return {
        "status": status, 
        "index_loaded": faiss_index is not None, 
        "chunk_count": chunk_count_val,
        "cache_size": cache_stats['size'],
        "cache_enabled": True
    }



# Run the server
if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8001)