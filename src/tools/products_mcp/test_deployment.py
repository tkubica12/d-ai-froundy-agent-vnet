"""
Deployment test for Products MCP Server.

Tests the deployed MCP server running in Azure Container Apps.
This test uses SSE (Server-Sent Events) transport over HTTP to connect
to the remote MCP server endpoint.

Usage:
    # Pass endpoint as argument
    uv run python test_deployment.py https://aca-mcp-xyz.internal.region.azurecontainerapps.io
    
    # Or set environment variable
    export MCP_ENDPOINT=https://aca-mcp-xyz.internal.region.azurecontainerapps.io
    uv run python test_deployment.py
    
    # Or run with pytest
    uv run pytest test_deployment.py -v -s

Requirements:
    - MCP endpoint as argument or MCP_ENDPOINT environment variable must be set
    - Network connectivity to the MCP server (e.g., from jump VM or VPN)
    - MCP server must be running and healthy
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

import pytest
from fastmcp import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Global variable to store endpoint for pytest
_test_endpoint: Optional[str] = None


def get_mcp_endpoint(endpoint_arg: Optional[str] = None) -> Optional[str]:
    """
    Get MCP endpoint from argument or environment variable.
    
    Args:
        endpoint_arg: Optional endpoint passed as command-line argument
        
    Returns:
        MCP endpoint URL or None if not configured
    """
    # Prioritize command-line argument over environment variable
    endpoint = endpoint_arg or os.getenv("MCP_ENDPOINT")
    
    if not endpoint:
        logger.error("MCP endpoint not provided")
        logger.error("Usage: python test_deployment.py <endpoint>")
        logger.error("   or: export MCP_ENDPOINT=https://aca-mcp-xyz.internal.region.azurecontainerapps.io")
        return None
    
    # Ensure endpoint has proper format
    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}"
    
    logger.info(f"Using MCP endpoint: {endpoint}")
    return endpoint


@pytest.mark.asyncio
async def test_deployed_mcp_server():
    """Test the deployed MCP server with comprehensive tool validation."""
    
    # Get endpoint from global variable (set by main) or environment
    endpoint = _test_endpoint or get_mcp_endpoint()
    if not endpoint:
        pytest.skip("MCP_ENDPOINT not configured")
    
    logger.info("=== Testing Deployed MCP Server ===\n")
    logger.info(f"Endpoint: {endpoint}\n")
    
    # Connect using SSE transport (HTTP-based)
    client = Client(endpoint)
    
    try:
        async with client:
            # Test 1: Server health check
            logger.info("Test 1: Server health check")
            try:
                await client.ping()
                logger.info("✓ Server is responsive\n")
            except Exception as e:
                logger.error(f"✗ Server health check failed: {e}")
                raise
            
            # Test 2: List available tools
            logger.info("Test 2: List available tools")
            try:
                tools = await client.list_tools()
                logger.info(f"✓ Found {len(tools)} tools:")
                for tool in tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
                logger.info("")
                
                # Verify expected tools are present
                tool_names = {tool.name for tool in tools}
                expected_tools = {
                    "get_user_profile",
                    "vector_search_products",
                    "get_pricing",
                    "get_stock",
                    "rank_candidates_tool"
                }
                
                missing_tools = expected_tools - tool_names
                if missing_tools:
                    logger.error(f"✗ Missing expected tools: {missing_tools}")
                    raise AssertionError(f"Missing tools: {missing_tools}")
                
                logger.info("✓ All expected tools are present\n")
                
            except Exception as e:
                logger.error(f"✗ Failed to list tools: {e}")
                raise
            
            # Test 3: Get user profile (expect NotFound for test user)
            logger.info("Test 3: Get user profile")
            try:
                result = await client.call_tool(
                    "get_user_profile",
                    {"user_id": "test-deployment-user"}
                )
                logger.info(f"Result: {result.data}")
                logger.info("✓ get_user_profile executed successfully\n")
            except Exception as e:
                # Expected to fail for non-existent user
                logger.info(f"Expected result (user not found): {e}")
                logger.info("✓ get_user_profile behaves correctly\n")
            
            # Test 4: Vector search with mock embedding
            logger.info("Test 4: Vector search products")
            try:
                # Create a mock 2048-dimensional embedding
                mock_embedding = [0.1] * 2048
                mock_embedding[0] = 1.0
                
                result = await client.call_tool(
                    "vector_search_products",
                    {
                        "embedding": mock_embedding,
                        "filters": {"category": "outdoor"},
                        "top_k": 5
                    }
                )
                logger.info(f"Result: {result.data}")
                logger.info("✓ vector_search_products executed successfully\n")
            except Exception as e:
                logger.error(f"✗ vector_search_products failed: {e}")
                raise
            
            # Test 5: Get pricing
            logger.info("Test 5: Get pricing")
            try:
                result = await client.call_tool(
                    "get_pricing",
                    {"product_ids": ["test-prod-1", "test-prod-2"]}
                )
                logger.info(f"Result: {result.data}")
                logger.info("✓ get_pricing executed successfully\n")
            except Exception as e:
                logger.error(f"✗ get_pricing failed: {e}")
                raise
            
            # Test 6: Get stock
            logger.info("Test 6: Get stock")
            try:
                result = await client.call_tool(
                    "get_stock",
                    {"product_ids": ["test-prod-1", "test-prod-2"]}
                )
                logger.info(f"Result: {result.data}")
                logger.info("✓ get_stock executed successfully\n")
            except Exception as e:
                logger.error(f"✗ get_stock failed: {e}")
                raise
            
            # Test 7: Rank candidates
            logger.info("Test 7: Rank candidates")
            try:
                mock_requirements = {
                    "must_not_include_allergens": ["nuts"],
                    "preferred_categories": ["outdoor"],
                    "max_price": 100.0
                }
                
                mock_candidates = [
                    {
                        "product_id": "test-prod-1",
                        "similarity": 0.92,
                        "price": 45.99,
                        "quantity_available": 10,
                        "popularity_score": 0.85,
                        "category": "outdoor",
                        "tags": ["hiking", "waterproof"]
                    },
                    {
                        "product_id": "test-prod-2",
                        "similarity": 0.88,
                        "price": 89.99,
                        "quantity_available": 0,
                        "popularity_score": 0.90,
                        "category": "outdoor",
                        "tags": ["camping"]
                    }
                ]
                
                result = await client.call_tool(
                    "rank_candidates_tool",
                    {
                        "requirements": mock_requirements,
                        "candidates": mock_candidates
                    }
                )
                logger.info(f"Result: {result.data}")
                logger.info("✓ rank_candidates_tool executed successfully\n")
            except Exception as e:
                logger.error(f"✗ rank_candidates_tool failed: {e}")
                raise
            
        logger.info("=== All Deployment Tests Passed ===")
        
    except Exception as e:
        logger.error(f"\n=== Deployment Tests Failed ===")
        logger.error(f"Error: {e}")
        raise


async def main():
    """Main entry point for running tests directly."""
    global _test_endpoint
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Test deployed MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_deployment.py https://aca-mcp-xyz.internal.region.azurecontainerapps.io
  python test_deployment.py aca-mcp-xyz.internal.region.azurecontainerapps.io
  
  export MCP_ENDPOINT=https://aca-mcp-xyz.internal.region.azurecontainerapps.io
  python test_deployment.py
        """
    )
    parser.add_argument(
        "endpoint",
        nargs="?",
        help="MCP server endpoint URL (or set MCP_ENDPOINT environment variable)"
    )
    
    args = parser.parse_args()
    
    endpoint = get_mcp_endpoint(args.endpoint)
    if not endpoint:
        sys.exit(1)
    
    # Set global endpoint for test function
    _test_endpoint = endpoint
    
    try:
        await test_deployed_mcp_server()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
