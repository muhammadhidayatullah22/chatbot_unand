#!/usr/bin/env python3
"""
Rebuild FAISS index with all documents
"""
import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv()

# Import after loading env
from main import preprocess_documents_and_build_index, FAISS_INDEX_PATH, DOC_CHUNKS_PATH, VECTOR_DB_DIR, DATA_DIR
import asyncio

async def rebuild_index():
    print("🔄 Rebuilding FAISS index with all documents...")
    
    # Check how many documents we have
    doc_count = 0
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".docx") and not filename.startswith("~$"):
            doc_count += 1
            print(f"📄 Found document: {filename}")
    
    print(f"\n📊 Total documents found: {doc_count}")
    
    if doc_count == 0:
        print("❌ No documents found in data folder!")
        return
    
    # Remove existing index to force rebuild
    if os.path.exists(FAISS_INDEX_PATH):
        print(f"🗑️ Removing existing FAISS index: {FAISS_INDEX_PATH}")
        os.remove(FAISS_INDEX_PATH)
    
    if os.path.exists(DOC_CHUNKS_PATH):
        print(f"🗑️ Removing existing doc chunks: {DOC_CHUNKS_PATH}")
        os.remove(DOC_CHUNKS_PATH)
    
    # Rebuild index
    print("\n🚀 Starting document processing...")
    await preprocess_documents_and_build_index()
    
    # Check results
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(DOC_CHUNKS_PATH):
        print("✅ FAISS index rebuilt successfully!")
        
        # Load and check chunks
        import json
        with open(DOC_CHUNKS_PATH, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"📈 Total chunks created: {len(chunks)}")
        
        # Count chunks per document
        doc_chunks = {}
        for chunk in chunks:
            filename = chunk.get('filename', 'Unknown')
            if filename not in doc_chunks:
                doc_chunks[filename] = 0
            doc_chunks[filename] += 1
        
        print("\n📋 Chunks per document:")
        for filename, count in sorted(doc_chunks.items()):
            print(f"  📄 {filename}: {count} chunks")
            
    else:
        print("❌ Failed to rebuild FAISS index!")

if __name__ == "__main__":
    asyncio.run(rebuild_index())
