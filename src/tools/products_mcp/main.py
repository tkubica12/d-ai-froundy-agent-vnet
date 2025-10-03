"""
Products MCP Server

FastMCP-based Model Context Protocol server that exposes product catalog tools
for Azure AI Foundry agents. Provides vector search, pricing, stock, and ranking
capabilities backed by Azure Cosmos DB.

All operations use Azure Managed Identity authentication when deployed to Azure.
"""

import logging
from typing import Any
from fastmcp import FastMCP

from config import settings
from cosmos_client import get_cosmos_client
from models import (
    UserProfile,
    VectorSearchRequest,
    VectorSearchResponse,
    ProductCandidate,
    PricingRequest,
    PricingResponse,
    PricingItem,
    StockRequest,
    StockResponse,
    StockItem,
    RankingRequest,
    RankingResponse,
    CandidateProduct,
    ErrorResponse,
    ErrorDetail,
)
from ranking import rank_candidates

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Initialize FastMCP server
mcp = FastMCP("products-mcp")


@mcp.tool()
async def get_user_profile(user_id: str) -> UserProfile | ErrorResponse:
    """
    Retrieve user profile by user_id.
    
    Args:
        user_id: Entra OID of the authenticated user
        
    Returns:
        UserProfile if found, ErrorResponse if not found
    """
    logger.info(f"get_user_profile called for user_id: {user_id}")
    
    try:
        cosmos = get_cosmos_client()
        profile_data = await cosmos.get_user_profile(user_id)
        
        if profile_data is None:
            return ErrorResponse(error=ErrorDetail(
                code="NotFound",
                message=f"Profile not found for user: {user_id}",
                details={"user_id": user_id}
            ))
        
        return UserProfile(**profile_data)
    
    except Exception as e:
        logger.exception("Error retrieving user profile")
        return ErrorResponse(error=ErrorDetail(
            code="InternalError",
            message=str(e),
            details={"user_id": user_id}
        ))


@mcp.tool()
async def vector_search_products(
    query_text: str | None = None,
    embedding: list[float] | None = None,
    filters: dict[str, Any] | None = None,
    top_k: int = 20
) -> VectorSearchResponse | ErrorResponse:
    """
    Perform vector similarity search on product catalog.
    
    Either query_text or embedding must be provided. If query_text is provided,
    it should be embedded externally before calling this tool.
    
    Args:
        query_text: Natural language query (for reference - not embedded here)
        embedding: Pre-computed embedding vector (1536 dimensions)
        filters: Optional filters like {"category": "outdoor"}
        top_k: Number of candidates to return (default: 20)
        
    Returns:
        VectorSearchResponse with product candidates and similarity scores
    """
    logger.info(f"vector_search_products called with top_k={top_k}, filters={filters}")
    
    try:
        # Validate request
        request = VectorSearchRequest(
            query_text=query_text,
            embedding=embedding,
            filters=filters or {},
            top_k=top_k
        )
        
        if not request.embedding:
            return ErrorResponse(error=ErrorDetail(
                code="InvalidRequest",
                message="Embedding vector is required. query_text alone is not supported.",
                details={"query_text": query_text}
            ))
        
        # Perform vector search
        cosmos = get_cosmos_client()
        results = await cosmos.vector_search_products(
            embedding=request.embedding,
            filters=request.filters,
            top_k=request.top_k
        )
        
        # Convert to response model
        candidates = [
            ProductCandidate(
                product_id=item["id"],
                similarity=1.0 - item.get("similarity", 1.0)  # Convert distance to similarity
            )
            for item in results
        ]
        
        logger.info(f"Returned {len(candidates)} product candidates")
        return VectorSearchResponse(candidates=candidates)
    
    except ValueError as e:
        return ErrorResponse(error=ErrorDetail(
            code="ValidationError",
            message=str(e)
        ))
    except Exception as e:
        logger.exception("Error performing vector search")
        return ErrorResponse(error=ErrorDetail(
            code="InternalError",
            message=str(e)
        ))


@mcp.tool()
async def get_pricing(product_ids: list[str]) -> PricingResponse | ErrorResponse:
    """
    Retrieve current pricing for multiple products.
    
    Args:
        product_ids: List of product IDs to look up
        
    Returns:
        PricingResponse with current pricing information
    """
    logger.info(f"get_pricing called for {len(product_ids)} products")
    
    try:
        if not product_ids:
            return PricingResponse(pricing=[])
        
        cosmos = get_cosmos_client()
        pricing_data = await cosmos.get_pricing_batch(product_ids)
        
        # Convert to response model
        pricing_items = [
            PricingItem(
                product_id=item["product_id"],
                price=item["price"],
                currency=item.get("currency", "USD")
            )
            for item in pricing_data
        ]
        
        logger.info(f"Returned pricing for {len(pricing_items)} products")
        return PricingResponse(pricing=pricing_items)
    
    except Exception as e:
        logger.exception("Error retrieving pricing")
        return ErrorResponse(error=ErrorDetail(
            code="InternalError",
            message=str(e),
            details={"product_ids": product_ids}
        ))


@mcp.tool()
async def get_stock(product_ids: list[str]) -> StockResponse | ErrorResponse:
    """
    Retrieve current stock levels for multiple products.
    
    Args:
        product_ids: List of product IDs to look up
        
    Returns:
        StockResponse with current stock availability
    """
    logger.info(f"get_stock called for {len(product_ids)} products")
    
    try:
        if not product_ids:
            return StockResponse(stock=[])
        
        cosmos = get_cosmos_client()
        stock_data = await cosmos.get_stock_batch(product_ids)
        
        # Convert to response model
        stock_items = [
            StockItem(
                product_id=item["product_id"],
                quantity_available=item["quantity_available"]
            )
            for item in stock_data
        ]
        
        logger.info(f"Returned stock for {len(stock_items)} products")
        return StockResponse(stock=stock_items)
    
    except Exception as e:
        logger.exception("Error retrieving stock")
        return ErrorResponse(error=ErrorDetail(
            code="InternalError",
            message=str(e),
            details={"product_ids": product_ids}
        ))


@mcp.tool()
async def rank_candidates_tool(
    requirements: dict[str, Any],
    candidates: list[dict[str, Any]]
) -> RankingResponse | ErrorResponse:
    """
    Rank product candidates based on user requirements and heuristic scoring.
    
    Applies exclusion rules (allergens, out of stock, price limits) and scores
    remaining candidates using weighted heuristics for similarity, popularity,
    price affinity, and availability.
    
    Args:
        requirements: Normalized requirements from Facilitator agent
        candidates: Enriched candidate products with pricing and stock
        
    Returns:
        RankingResponse with primary recommendation and alternatives
    """
    logger.info(f"rank_candidates called with {len(candidates)} candidates")
    
    try:
        # Parse and validate inputs
        from models import Requirements, CandidateProduct
        
        reqs = Requirements(**requirements)
        candidate_objs = [CandidateProduct(**c) for c in candidates]
        
        # Perform ranking
        primary, alternatives = rank_candidates(reqs, candidate_objs)
        
        result = RankingResponse(
            primary=primary,
            alternatives=alternatives
        )
        
        logger.info(
            f"Ranking complete: primary={primary.product_id if primary else None}, "
            f"alternatives={len(alternatives)}"
        )
        return result
    
    except Exception as e:
        logger.exception("Error ranking candidates")
        return ErrorResponse(error=ErrorDetail(
            code="InternalError",
            message=str(e)
        ))


def main():
    """Run the MCP server in SSE mode on port 8080."""
    logger.info("Starting Products MCP Server")
    logger.info(f"Cosmos DB endpoint: {settings.cosmos_db_endpoint}")
    logger.info(f"Using Managed Identity: {settings.use_managed_identity}")
    logger.info("Starting SSE server on port 8080")
    
    # Always run in SSE mode for Azure Container Apps deployment
    mcp.run(transport="http", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
