"""
Configuration settings for the products MCP server.

Loads configuration from environment variables and .env file.
Uses Azure DefaultAzureCredential for authentication when COSMOS_DB_KEY is not provided.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Azure Cosmos DB Configuration
    cosmos_db_endpoint: str
    cosmos_db_name: str = "appdb"
    cosmos_db_key: str | None = None  # Optional: uses Managed Identity if not provided

    # Azure OpenAI / AI Foundry Configuration for Embeddings
    embeddings_endpoint: str | None = None  # Optional: endpoint for Azure OpenAI embeddings
    embeddings_deployment: str = "text-embedding-3-large"
    embeddings_dimensions: int = 2048  # Reduced from 3072 max to fit Cosmos DB limits
    embeddings_api_version: str = "2024-08-01-preview"

    # Vector Search Settings
    vector_top_k: int = 20
    min_similarity_threshold: float = 0.5

    # Ranking Weights (must sum to ~1.0)
    similarity_weight: float = 0.55
    popularity_weight: float = 0.15
    price_weight: float = 0.15
    availability_weight: float = 0.15

    # Logging
    log_level: str = "INFO"

        @property
    def use_managed_identity(self) -> bool:
        """Determine if we should use Managed Identity authentication."""
        return not self.cosmos_db_key or self.cosmos_db_key.strip() == ""

    @property
    def use_embeddings(self) -> bool:
        """Determine if embeddings endpoint is configured."""
        return self.embeddings_endpoint is not None and self.embeddings_endpoint.strip() != ""


settings = Settings()
