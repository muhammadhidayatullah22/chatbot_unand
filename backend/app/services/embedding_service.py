"""
Async Embedding Service - Non-blocking embedding generation
"""
import asyncio
import os
import numpy as np
from nomic import embed
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service untuk generate embedding secara async"""
    
    def __init__(self, api_key: str, model: str = "nomic-embed-text-v1.5", max_workers: int = 4):
        self.api_key = api_key
        self.model = model
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        # Authentication for Nomic SDK uses NOMIC_API_KEY env var
        if os.getenv("NOMIC_API_KEY") is None and api_key:
            # Allow passing api_key to set env for this process
            os.environ["NOMIC_API_KEY"] = api_key
    
    def _generate_embedding_sync(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        """Generate embedding secara synchronous (untuk thread pool)"""
        try:
            task = "search_query" if (task_type or "").upper().endswith("QUERY") else "search_document"
            model_for_nomic = (self.model or "nomic-embed-text-v1.5").split("/")[-1]
            out = embed.text(
                texts=[text],
                model=model_for_nomic,
                task_type=task,
                dimensionality=768,
            )
            vec = out.get("embeddings", [None])[0]
            if vec is None:
                raise ValueError(f"Unexpected response format from Nomic embed: {out}")
            return np.array(vec).astype('float32')
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embedding_async(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        """Generate embedding secara async (non-blocking)"""
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            self._generate_embedding_sync,
            text,
            task_type
        )
        return embedding
    
    async def generate_embeddings_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[np.ndarray]:
        """Generate multiple embeddings in one Nomic batch call"""
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._generate_embeddings_batch_sync,
            texts,
            task_type,
        )

    def _generate_embeddings_batch_sync(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[np.ndarray]:
        task = "search_document" if (task_type or "").upper().endswith("DOCUMENT") else "search_query"
        model_for_nomic = (self.model or "nomic-embed-text-v1.5").split("/")[-1]
        out = embed.text(
            texts=texts,
            model=model_for_nomic,
            task_type=task,
            dimensionality=768,
        )
        embs = out.get("embeddings", [])
        if not embs or len(embs) != len(texts):
            raise ValueError(f"Failed to get embeddings for all inputs from Nomic: {len(embs)} vs {len(texts)}")
        return [np.array(v).astype('float32') for v in embs]
    
    def generate_embedding_sync(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        """Generate embedding secara sync (untuk backward compatibility)"""
        return self._generate_embedding_sync(text, task_type)
    
    def close(self):
        """Close thread pool executor"""
        self.executor.shutdown(wait=True)

