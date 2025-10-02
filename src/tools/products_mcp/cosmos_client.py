"""
Azure Cosmos DB client for product catalog operations.

Provides typed access to Cosmos DB collections with vector search capabilities.
Uses DefaultAzureCredential (Managed Identity) when no key is provided.
"""

import logging
from typing import Any
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential

from config import settings

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """
    Client for interacting with Azure Cosmos DB.
    
    Handles authentication via either key or Managed Identity,
    provides access to product, pricing, stock, and user_profiles collections.
    """

    def __init__(self):
        """Initialize Cosmos DB client with appropriate authentication."""
        if settings.use_managed_identity:
            logger.info("Using DefaultAzureCredential for Cosmos DB authentication")
            credential = DefaultAzureCredential()
            self.client = CosmosClient(settings.cosmos_db_endpoint, credential=credential)
        else:
            logger.info("Using key-based authentication for Cosmos DB")
            self.client = CosmosClient(settings.cosmos_db_endpoint, credential=settings.cosmos_db_key)
        
        self.database = self.client.get_database_client(settings.cosmos_db_name)
        self.products = self.database.get_container_client("products")
        self.pricing = self.database.get_container_client("pricing")
        self.stock = self.database.get_container_client("stock")
        self.user_profiles = self.database.get_container_client("user_profiles")
        
        logger.info(f"Connected to Cosmos DB: {settings.cosmos_db_name}")

    async def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """
        Retrieve user profile by user_id.
        
        Args:
            user_id: Entra OID of the user
            
        Returns:
            User profile dict or None if not found
        """
        try:
            item = self.user_profiles.read_item(item=user_id, partition_key=user_id)
            logger.debug(f"Retrieved profile for user: {user_id}")
            return item
        except CosmosResourceNotFoundError:
            logger.debug(f"Profile not found for user: {user_id}")
            return None

    async def vector_search_products(
        self,
        embedding: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 20
    ) -> list[dict[str, Any]]:
        """
        Perform vector similarity search on products.
        
        Args:
            embedding: Query embedding vector (1536 dimensions)
            filters: Optional filters (e.g., {"category": "outdoor"})
            top_k: Number of results to return
            
        Returns:
            List of products with similarity scores
        """
        # Build query with vector search
        query = """
            SELECT TOP @top_k 
                c.id,
                c.name,
                c.category,
                c.tags,
                c.popularity_score,
                VectorDistance(c.embedding, @embedding) AS similarity
            FROM c
        """
        
        parameters = [
            {"name": "@embedding", "value": embedding},
            {"name": "@top_k", "value": top_k}
        ]
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            if "category" in filters:
                filter_clauses.append("c.category = @category")
                parameters.append({"name": "@category", "value": filters["category"]})
            
            if filter_clauses:
                query += " WHERE " + " AND ".join(filter_clauses)
        
        query += " ORDER BY VectorDistance(c.embedding, @embedding)"
        
        items = list(self.products.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Vector search returned {len(items)} candidates")
        return items

    async def get_pricing_batch(self, product_ids: list[str]) -> list[dict[str, Any]]:
        """
        Retrieve pricing for multiple products.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            List of pricing records (active/current pricing only)
        """
        if not product_ids:
            return []
        
        # Build IN clause for query
        placeholders = ", ".join([f"@id{i}" for i in range(len(product_ids))])
        query = f"""
            SELECT c.product_id, c.price, c.currency
            FROM c
            WHERE c.product_id IN ({placeholders})
              AND (c.effective_to = null OR c.effective_to > GetCurrentDateTime())
        """
        
        parameters = [
            {"name": f"@id{i}", "value": pid}
            for i, pid in enumerate(product_ids)
        ]
        
        items = list(self.pricing.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logger.debug(f"Retrieved pricing for {len(items)}/{len(product_ids)} products")
        return items

    async def get_stock_batch(self, product_ids: list[str]) -> list[dict[str, Any]]:
        """
        Retrieve stock information for multiple products.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            List of stock records
        """
        if not product_ids:
            return []
        
        placeholders = ", ".join([f"@id{i}" for i in range(len(product_ids))])
        query = f"""
            SELECT c.product_id, c.quantity_available
            FROM c
            WHERE c.product_id IN ({placeholders})
        """
        
        parameters = [
            {"name": f"@id{i}", "value": pid}
            for i, pid in enumerate(product_ids)
        ]
        
        items = list(self.stock.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logger.debug(f"Retrieved stock for {len(items)}/{len(product_ids)} products")
        return items


# Global client instance
_cosmos_client: CosmosDBClient | None = None


def get_cosmos_client() -> CosmosDBClient:
    """Get or create the global Cosmos DB client instance."""
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosDBClient()
    return _cosmos_client
