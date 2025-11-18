#!/usr/bin/env python3
import os
import faiss
from dotenv import load_dotenv

load_dotenv()

# Load index
index_path = os.path.join(os.path.dirname(__file__), "vector_db", "faiss_index.bin")

if os.path.exists(index_path):
    index = faiss.read_index(index_path)
    print(f"✅ Index loaded successfully")
    print(f"📊 Index dimension: {index.d}")
    print(f"📈 Total vectors: {index.ntotal}")
    
    # Expected dimension
    embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5")
    # Standardize to 768-dim embeddings (Nomic)
    expected_dim = 768
    
    if index.d == expected_dim:
        print(f"✅ Dimension matches! ({index.d} == {expected_dim})")
    else:
        print(f"❌ Dimension mismatch! Index: {index.d}, Expected: {expected_dim}")
else:
    print("❌ Index file not found!")