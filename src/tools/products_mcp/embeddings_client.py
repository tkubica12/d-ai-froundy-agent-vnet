"""
Azure OpenAI embeddings client.

Provides text embedding generation using Azure AI Foundry deployed models.
Uses DefaultAzureCredential for authentication (managed identity).
"""

import logging
from typing import Any
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

from config import settings

logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)


class EmbeddingsClient:
    """Client for generating text embeddings using Azure OpenAI."""

    def __init__(self):
        """Initialize the embeddings client with managed identity authentication."""
        if not settings.use_embeddings:
            logger.warning("Embeddings endpoint not configured - embeddings generation disabled")
            self.client = None
            return

        logger.info(f"Initializing Azure OpenAI embeddings client: {settings.embeddings_endpoint}")
        
        # Use DefaultAzureCredential for authentication
        credential = DefaultAzureCredential()
        token_provider = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        self.client = AzureOpenAI(
            azure_endpoint=settings.embeddings_endpoint,
            api_version=settings.embeddings_api_version,
            azure_ad_token=token_provider.token,
        )
        
        logger.info(f"Embeddings client initialized - deployment: {settings.embeddings_deployment}, dimensions: {settings.embeddings_dimensions}")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector with dimensions specified in settings
            
        Raises:
            RuntimeError: If embeddings client is not configured
            Exception: If embedding generation fails
        """
        if self.client is None:
            raise RuntimeError("Embeddings client not configured - set EMBEDDINGS_ENDPOINT in .env")
        
        try:
            response = self.client.embeddings.create(
                model=settings.embeddings_deployment,
                input=text,
                dimensions=settings.embeddings_dimensions
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single batch request.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If embeddings client is not configured
            Exception: If embedding generation fails
        """
        if self.client is None:
            raise RuntimeError("Embeddings client not configured - set EMBEDDINGS_ENDPOINT in .env")
        
        try:
            response = self.client.embeddings.create(
                model=settings.embeddings_deployment,
                input=texts,
                dimensions=settings.embeddings_dimensions
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings batch: {e}")
            raise


# Global embeddings client instance
_embeddings_client: EmbeddingsClient | None = None


def get_embeddings_client() -> EmbeddingsClient:
    """
    Get or create the global embeddings client instance.
    
    Returns:
        EmbeddingsClient instance
    """
    global _embeddings_client
    
    if _embeddings_client is None:
        _embeddings_client = EmbeddingsClient()
    
    return _embeddings_client
