"""
Async Embedding Service - Non-blocking embedding generation
"""
import asyncio
import numpy as np
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service untuk generate embedding secara async"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-large", max_workers: int = 4):
        self.api_key = api_key
        self.model = model
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    
    def _generate_embedding_sync(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        """Generate embedding secara synchronous (untuk thread pool)"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            if not response.data or not getattr(response.data[0], 'embedding', None):
                raise ValueError(f"Unexpected response format: {response}")
            return np.array(response.data[0].embedding).astype('float32')
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
        """Generate multiple embeddings secara parallel"""
        tasks = [
            self.generate_embedding_async(text, task_type)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
    
    def generate_embedding_sync(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> np.ndarray:
        """Generate embedding secara sync (untuk backward compatibility)"""
        return self._generate_embedding_sync(text, task_type)
    
    def close(self):
        """Close thread pool executor"""
        self.executor.shutdown(wait=True)

