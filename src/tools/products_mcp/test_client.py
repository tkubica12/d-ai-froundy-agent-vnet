"""
Testing utility for the Products MCP Server.

Uses FastMCP client to test all tools with mock data.
Demonstrates in-memory transport for quick testing without network complexity.
"""

import asyncio
import logging
from fastmcp import Client, FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)


async def test_server():
    """Test all MCP server tools with sample data."""
    
    # Import the server
    from main import mcp
    
    # Create client with in-memory transport (ideal for testing)
    client = Client(mcp)
    
    logger.info("=== Starting MCP Server Tests ===\n")
    
    async with client:
        # Test 1: Ping server
        logger.info("Test 1: Ping server")
        await client.ping()
        logger.info("✓ Server is responsive\n")
        
        # Test 2: List available tools
        logger.info("Test 2: List available tools")
        tools = await client.list_tools()
        logger.info(f"Available tools: {len(tools)}")
        for tool in tools:
            logger.info(f"  - {tool.name}: {tool.description}")
        logger.info("")
        
        # Test 3: Get user profile (should return NotFound for test user)
        logger.info("Test 3: Get user profile")
        try:
            result = await client.call_tool(
                "get_user_profile",
                {"user_id": "test-user-123"}
            )
            logger.info(f"Result: {result.data}")
        except Exception as e:
            logger.error(f"Error: {e}")
        logger.info("")
        
        # Test 4: Vector search (with mock embedding)
        logger.info("Test 4: Vector search products")
        # Create a mock 1536-dimensional embedding (all zeros for testing)
        mock_embedding = [0.0] * 1536
        mock_embedding[0] = 1.0  # Make it slightly non-zero
        
        try:
            result = await client.call_tool(
                "vector_search_products",
                {
                    "embedding": mock_embedding,
                    "filters": {"category": "outdoor"},
                    "top_k": 10
                }
            )
            logger.info(f"Result: {result.data}")
        except Exception as e:
            logger.error(f"Error: {e}")
        logger.info("")
        
        # Test 5: Get pricing
        logger.info("Test 5: Get pricing")
        try:
            result = await client.call_tool(
                "get_pricing",
                {"product_ids": ["prod-1", "prod-2", "prod-3"]}
            )
            logger.info(f"Result: {result.data}")
        except Exception as e:
            logger.error(f"Error: {e}")
        logger.info("")
        
        # Test 6: Get stock
        logger.info("Test 6: Get stock")
        try:
            result = await client.call_tool(
                "get_stock",
                {"product_ids": ["prod-1", "prod-2", "prod-3"]}
            )
            logger.info(f"Result: {result.data}")
        except Exception as e:
            logger.error(f"Error: {e}")
        logger.info("")
        
        # Test 7: Rank candidates
        logger.info("Test 7: Rank candidates")
        mock_requirements = {
            "must_not_include_allergens": ["nuts"],
            "preferred_categories": ["outdoor"],
            "max_price": 100.0
        }
        
        mock_candidates = [
            {
                "product_id": "prod-1",
                "similarity": 0.92,
                "price": 45.99,
                "quantity_available": 10,
                "popularity_score": 0.85,
                "category": "outdoor",
                "tags": ["hiking", "waterproof"]
            },
            {
                "product_id": "prod-2",
                "similarity": 0.88,
                "price": 89.99,
                "quantity_available": 0,
                "popularity_score": 0.90,
                "category": "outdoor",
                "tags": ["camping"]
            },
            {
                "product_id": "prod-3",
                "similarity": 0.85,
                "price": 120.00,
                "quantity_available": 5,
                "popularity_score": 0.75,
                "category": "outdoor",
                "tags": ["climbing"]
            }
        ]
        
        try:
            result = await client.call_tool(
                "rank_candidates_tool",
                {
                    "requirements": mock_requirements,
                    "candidates": mock_candidates
                }
            )
            logger.info(f"Result: {result.data}")
        except Exception as e:
            logger.error(f"Error: {e}")
        logger.info("")
        
    logger.info("=== All Tests Complete ===")


async def test_with_external_server(server_path: str = "./main.py"):
    """
    Test with external server using stdio transport.
    
    This launches the server as a subprocess and communicates via stdio.
    
    Args:
        server_path: Path to the server script
    """
    logger.info(f"=== Testing with external server: {server_path} ===\n")
    
    client = Client(server_path)
    
    async with client:
        logger.info("Connected to external server")
        await client.ping()
        logger.info("✓ Server is responsive\n")
        
        # List tools
        tools = await client.list_tools()
        logger.info(f"Available tools: {len(tools)}")
        for tool in tools:
            logger.info(f"  - {tool.name}")
        
    logger.info("\n=== External server test complete ===")


def main():
    """Run all tests."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--external":
        # Test with external server
        asyncio.run(test_with_external_server())
    else:
        # Test with in-memory server (default)
        asyncio.run(test_server())


if __name__ == "__main__":
    main()
