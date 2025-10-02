"""
Seed demo data into Cosmos DB.

Populates products, pricing, stock, and user_profiles collections
with realistic demo data for testing and development.

This script is IDEMPOTENT - it can be run multiple times safely:
- Deletes all existing documents in each collection before seeding
- Uses real embeddings from Azure OpenAI if configured, otherwise uses mock embeddings
- Verifies data after seeding

Usage:
    uv run python seed_data.py

Requirements:
    - Azure CLI authentication (az login) OR valid COSMOS_DB_KEY
    - Cosmos DB RBAC access (Data Contributor role) if using managed identity
    - (Optional) EMBEDDINGS_ENDPOINT configured for real embeddings
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
import random

from cosmos_client import get_cosmos_client
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logging
logging.getLogger("azure").setLevel(logging.ERROR)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.ERROR)
logging.getLogger("azure.cosmos").setLevel(logging.ERROR)

# Suppress verbose HTTP client logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Suppress embeddings client ERROR logs
logging.getLogger("embeddings_client").setLevel(logging.WARNING)


# Demo product data matching SolutionDesign.md schema
DEMO_PRODUCTS = [
    {
        "id": "prod-001",
        "name": "TrailBlazer Hiking Boots",
        "category": "outdoor",
        "tags": ["hiking", "waterproof", "durable"],
        "attributes": {
            "material": "leather",
            "color": "brown",
            "weight_oz": 28,
            "waterproof": True,
            "size_range": "6-14"
        },
        "popularity_score": 0.92,
        "description": "Premium waterproof hiking boots for serious trail enthusiasts"
    },
    {
        "id": "prod-002",
        "name": "Alpine Pro Backpack 45L",
        "category": "outdoor",
        "tags": ["backpack", "camping", "waterproof"],
        "attributes": {
            "capacity_liters": 45,
            "color": "green",
            "weight_oz": 48,
            "frame_type": "internal",
            "hydration_compatible": True
        },
        "popularity_score": 0.88,
        "description": "Versatile backpack for multi-day hiking and camping trips"
    },
    {
        "id": "prod-003",
        "name": "Summit Sleeping Bag -20F",
        "category": "outdoor",
        "tags": ["camping", "sleeping", "winter"],
        "attributes": {
            "temperature_rating": -20,
            "fill_type": "down",
            "color": "blue",
            "weight_oz": 56,
            "compression_sack": True
        },
        "popularity_score": 0.85,
        "description": "Cold-weather sleeping bag with premium 850-fill down insulation"
    },
    {
        "id": "prod-004",
        "name": "QuickDry Performance Tee",
        "category": "apparel",
        "tags": ["clothing", "moisture-wicking", "athletic"],
        "attributes": {
            "material": "polyester",
            "fit": "athletic",
            "colors": ["black", "navy", "gray"],
            "uv_protection": "UPF 50+"
        },
        "popularity_score": 0.78,
        "description": "Lightweight moisture-wicking shirt for active outdoor pursuits"
    },
    {
        "id": "prod-005",
        "name": "Canyon Trail Running Shoes",
        "category": "footwear",
        "tags": ["running", "trail", "lightweight"],
        "attributes": {
            "terrain": "trail",
            "drop_mm": 8,
            "weight_oz": 18,
            "color": "red",
            "grip_type": "aggressive lugs"
        },
        "popularity_score": 0.90,
        "description": "Agile trail running shoes with excellent traction on technical terrain"
    },
    {
        "id": "prod-006",
        "name": "Wilderness First Aid Kit",
        "category": "safety",
        "tags": ["emergency", "medical", "camping"],
        "attributes": {
            "items_count": 120,
            "weight_oz": 16,
            "waterproof": True,
            "includes_cpr_mask": True
        },
        "popularity_score": 0.75,
        "description": "Comprehensive first aid kit designed for outdoor adventures"
    },
    {
        "id": "prod-007",
        "name": "SolarCharge Power Bank 20000mAh",
        "category": "electronics",
        "tags": ["solar", "charging", "portable"],
        "attributes": {
            "capacity_mah": 20000,
            "solar_panel": True,
            "weight_oz": 14,
            "waterproof": True,
            "usb_ports": 2
        },
        "popularity_score": 0.82,
        "description": "Solar-powered portable charger for extended off-grid adventures"
    },
    {
        "id": "prod-008",
        "name": "Mountain Peak Tent 2P",
        "category": "outdoor",
        "tags": ["camping", "tent", "lightweight"],
        "attributes": {
            "capacity_persons": 2,
            "weight_oz": 80,
            "seasons": 3,
            "color": "orange",
            "freestanding": True
        },
        "popularity_score": 0.87,
        "description": "Lightweight 2-person tent perfect for backcountry camping"
    },
    {
        "id": "prod-009",
        "name": "Trail Mix Energy Bars (12 pack)",
        "category": "food",
        "tags": ["snacks", "energy", "nuts", "protein"],
        "attributes": {
            "count": 12,
            "calories_per_bar": 200,
            "contains": ["nuts", "dried fruit", "chocolate"],
            "allergens": ["nuts", "soy"]
        },
        "popularity_score": 0.70,
        "description": "Nutritious energy bars with nuts, dried fruit, and dark chocolate"
    },
    {
        "id": "prod-010",
        "name": "Hydration Bladder 3L",
        "category": "accessories",
        "tags": ["hydration", "water", "hiking"],
        "attributes": {
            "capacity_liters": 3,
            "bpa_free": True,
            "weight_oz": 6,
            "insulated": False,
            "leak_proof": True
        },
        "popularity_score": 0.80,
        "description": "Durable hydration bladder compatible with most backpacks"
    },
    {
        "id": "prod-011",
        "name": "Compass Navigation Set",
        "category": "navigation",
        "tags": ["compass", "navigation", "survival"],
        "attributes": {
            "includes_mirror": True,
            "luminous": True,
            "weight_oz": 2,
            "waterproof": True
        },
        "popularity_score": 0.65,
        "description": "Professional-grade compass with clinometer for backcountry navigation"
    },
    {
        "id": "prod-012",
        "name": "Insulated Water Bottle 32oz",
        "category": "accessories",
        "tags": ["water", "insulated", "stainless steel"],
        "attributes": {
            "capacity_oz": 32,
            "material": "stainless steel",
            "insulation_hours": 24,
            "colors": ["black", "silver", "blue"],
            "bpa_free": True
        },
        "popularity_score": 0.84,
        "description": "Double-wall vacuum insulated bottle keeps drinks cold for 24 hours"
    }
]


def generate_embedding(product: dict[str, Any]) -> list[float]:
    """
    Generate an embedding vector for a product using Azure OpenAI.
    
    Args:
        product: Product dictionary with id, name, tags, etc.
        
    Returns:
        Embedding vector with configured dimensions
        
    Raises:
        RuntimeError: If embeddings endpoint is not configured
        Exception: If embedding generation fails
    """
    if not settings.use_embeddings:
        raise RuntimeError("Embeddings endpoint not configured - set EMBEDDINGS_ENDPOINT in .env")
    
    from embeddings_client import get_embeddings_client
    
    # Create rich text representation for embedding
    text_parts = [
        product["name"],
        product.get("description", ""),
        f"Category: {product.get('category', '')}",
        f"Tags: {', '.join(product.get('tags', []))}",
    ]
    
    # Add key attributes
    if "attributes" in product:
        attrs = product["attributes"]
        for key, value in attrs.items():
            text_parts.append(f"{key}: {value}")
    
    text = " | ".join(filter(None, text_parts))
    
    embeddings_client = get_embeddings_client()
    embedding = embeddings_client.generate_embedding(text)
    
    logger.debug(f"Generated embedding for {product['id']} ({len(embedding)} dimensions)")
    return embedding


async def clear_collection(container, collection_name: str) -> int:
    """
    Delete all documents from a collection (idempotent cleanup).
    
    Args:
        container: Cosmos DB container client
        collection_name: Name of the collection for logging
        
    Returns:
        Number of documents deleted
    """
    logger.info(f"Clearing {collection_name} collection...")
    count = 0
    
    try:
        # Query all document IDs
        query = "SELECT c.id, c.category FROM c" if collection_name == "products" else "SELECT c.id FROM c"
        items = list(container.query_items(query, enable_cross_partition_query=True))
        
        if not items:
            logger.info(f"  {collection_name} is already empty")
            return 0
        
        # Delete each document
        for item in items:
            try:
                # Determine partition key based on collection
                if collection_name == "products":
                    partition_key = item.get("category", "")
                elif collection_name == "pricing" or collection_name == "stock":
                    # Need to fetch full document to get product_id
                    full_item = container.read_item(item["id"], partition_key=item["id"])
                    partition_key = full_item.get("product_id", "")
                elif collection_name == "user_profiles":
                    # Need to fetch full document to get user_id
                    full_item = container.read_item(item["id"], partition_key=item["id"])
                    partition_key = full_item.get("user_id", "")
                else:
                    partition_key = item["id"]
                
                container.delete_item(item["id"], partition_key=partition_key)
                count += 1
            except Exception as e:
                # Silently skip NotFound errors (document already deleted)
                if "NotFound" not in str(e):
                    logger.warning(f"  Failed to delete {item['id']}: {e}")
        
        logger.info(f"  Deleted {count} documents from {collection_name}")
        
    except Exception as e:
        logger.error(f"  Failed to clear {collection_name}: {e}")
    
    return count


async def seed_products(client) -> int:
    """Seed products collection with demo data (idempotent - clears first)."""
    await clear_collection(client.products, "products")
    
    logger.info("Seeding products collection...")
    count = 0
    
    for product in DEMO_PRODUCTS:
        product_doc = {
            **product,
            "embedding": generate_embedding(product),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "updated_utc": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            client.products.upsert_item(product_doc)
            count += 1
            logger.info(f"  ✓ {product['id']}: {product['name']}")
        except Exception as e:
            logger.error(f"  ✗ Failed to insert {product['id']}: {e}")
    
    logger.info(f"Seeded {count}/{len(DEMO_PRODUCTS)} products")
    return count


async def seed_pricing(client) -> int:
    """Seed pricing collection with demo data (idempotent - clears first)."""
    await clear_collection(client.pricing, "pricing")
    
    logger.info("Seeding pricing collection...")
    count = 0
    
    # Base prices for products (matching SolutionDesign.md schema)
    prices = {
        "prod-001": 159.99,
        "prod-002": 189.99,
        "prod-003": 249.99,
        "prod-004": 34.99,
        "prod-005": 129.99,
        "prod-006": 49.99,
        "prod-007": 79.99,
        "prod-008": 299.99,
        "prod-009": 24.99,
        "prod-010": 39.99,
        "prod-011": 45.99,
        "prod-012": 42.99
    }
    
    for product_id, price in prices.items():
        pricing_doc = {
            "id": f"price-{product_id}",
            "product_id": product_id,
            "price": price,
            "currency": "USD",
            "effective_from": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "effective_to": None  # Current/active pricing
        }
        
        try:
            client.pricing.upsert_item(pricing_doc)
            count += 1
            logger.info(f"  ✓ {product_id}: ${price}")
        except Exception as e:
            logger.error(f"  ✗ Failed to insert pricing for {product_id}: {e}")
    
    logger.info(f"Seeded {count}/{len(prices)} pricing records")
    return count


async def seed_stock(client) -> int:
    """Seed stock collection with demo data (idempotent - clears first)."""
    await clear_collection(client.stock, "stock")
    
    logger.info("Seeding stock collection...")
    count = 0
    
    # Stock levels (matching SolutionDesign.md schema)
    # Some items are out of stock for testing exclusion logic
    stock_levels = {
        "prod-001": 15,
        "prod-002": 8,
        "prod-003": 0,  # Out of stock - tests exclusion
        "prod-004": 50,
        "prod-005": 22,
        "prod-006": 12,
        "prod-007": 5,
        "prod-008": 0,  # Out of stock - tests exclusion
        "prod-009": 100,
        "prod-010": 30,
        "prod-011": 18,
        "prod-012": 25
    }
    
    warehouses = ["US-EAST", "US-WEST", "EU-WEST"]
    
    for product_id, quantity in stock_levels.items():
        # Randomly assign 1-2 warehouse locations
        available_warehouses = random.sample(warehouses, k=random.randint(1, 2)) if quantity > 0 else []
        
        stock_doc = {
            "id": f"stock-{product_id}",
            "product_id": product_id,
            "quantity_available": quantity,
            "warehouse_locations": available_warehouses,
            "last_updated_utc": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            client.stock.upsert_item(stock_doc)
            count += 1
            status = "OUT OF STOCK" if quantity == 0 else f"{quantity} units"
            logger.info(f"  ✓ {product_id}: {status} @ {', '.join(available_warehouses) if available_warehouses else 'N/A'}")
        except Exception as e:
            logger.error(f"  ✗ Failed to insert stock for {product_id}: {e}")
    
    logger.info(f"Seeded {count}/{len(stock_levels)} stock records")
    return count


async def seed_user_profiles(client) -> int:
    """Seed user_profiles collection with demo data (idempotent - clears first)."""
    await clear_collection(client.user_profiles, "user_profiles")
    
    logger.info("Seeding user_profiles collection...")
    count = 0
    
    # Demo user profiles (matching SolutionDesign.md schema)
    demo_profiles = [
        {
            "id": "user-alice",
            "user_id": "user-alice",  # Partition key
            "allergies": ["nuts"],
            "preferences": {
                "activity_level": "advanced",
                "preferred_brands": ["TrailBlazer", "Alpine Pro"],
                "budget": "premium"
            },
            "favorite_categories": ["outdoor", "footwear"],
            "hobbies": ["hiking", "mountaineering", "trail running"],
            "last_updated_utc": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-bob",
            "user_id": "user-bob",
            "allergies": [],
            "preferences": {
                "activity_level": "intermediate",
                "preferred_colors": ["black", "navy"],
                "budget": "mid-range"
            },
            "favorite_categories": ["outdoor", "camping"],
            "hobbies": ["camping", "fishing", "photography"],
            "last_updated_utc": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-carol",
            "user_id": "user-carol",
            "allergies": ["shellfish", "dairy"],
            "preferences": {
                "activity_level": "beginner",
                "diet": "vegetarian",
                "budget": "value"
            },
            "favorite_categories": ["apparel", "safety"],
            "hobbies": ["day hiking", "yoga", "nature walks"],
            "last_updated_utc": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-dave",
            "user_id": "user-dave",
            "allergies": ["soy"],
            "preferences": {
                "activity_level": "advanced",
                "sustainability": "eco-friendly",
                "budget": "premium"
            },
            "favorite_categories": ["electronics", "navigation"],
            "hobbies": ["backpacking", "orienteering", "wilderness survival"],
            "last_updated_utc": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for profile in demo_profiles:
        try:
            client.user_profiles.upsert_item(profile)
            count += 1
            allergies = ", ".join(profile['allergies']) if profile['allergies'] else "none"
            logger.info(f"  ✓ {profile['user_id']} (allergies: {allergies})")
        except Exception as e:
            logger.error(f"  ✗ Failed to insert profile {profile['user_id']}: {e}")
    
    logger.info(f"Seeded {count}/{len(demo_profiles)} user profiles")
    return count


async def verify_data(client):
    """Verify seeded data by running sample queries."""
    logger.info("\n" + "="*60)
    logger.info("Verifying seeded data...")
    logger.info("="*60)
    
    try:
        # Count products
        query = "SELECT VALUE COUNT(1) FROM c"
        result = list(client.products.query_items(query, enable_cross_partition_query=True))
        logger.info(f"  Products: {result[0]} documents")
        
        # Count pricing
        result = list(client.pricing.query_items(query, enable_cross_partition_query=True))
        logger.info(f"  Pricing: {result[0]} documents")
        
        # Count stock
        result = list(client.stock.query_items(query, enable_cross_partition_query=True))
        logger.info(f"  Stock: {result[0]} documents")
        
        # Count profiles
        result = list(client.user_profiles.query_items(query, enable_cross_partition_query=True))
        logger.info(f"  User Profiles: {result[0]} documents")
        
        # Test vector search (just verify it works)
        logger.info("\n  Testing vector search...")
        mock_embedding = [0.1] * 1536
        products = await get_cosmos_client().vector_search_products(
            embedding=mock_embedding,
            top_k=3
        )
        logger.info(f"  ✓ Vector search returned {len(products)} results")
        
        if products:
            for i, prod in enumerate(products[:3], 1):
                sim = 1.0 - prod.get('similarity', 1.0)
                logger.info(f"    {i}. {prod['name']} (similarity: {sim:.3f})")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Data verification complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main seeding function."""
    logger.info("="*60)
    logger.info("Cosmos DB Demo Data Seeding (Idempotent)")
    logger.info("="*60)
    logger.info(f"Endpoint: {settings.cosmos_db_endpoint}")
    logger.info(f"Database: {settings.cosmos_db_name}")
    logger.info(f"Auth: {'Managed Identity' if settings.use_managed_identity else 'Key'}")
    logger.info(f"Embeddings: {'Real (Azure OpenAI)' if settings.use_embeddings else 'Mock (random)'}")
    if settings.use_embeddings:
        logger.info(f"Embeddings Model: {settings.embeddings_deployment} ({settings.embeddings_dimensions}D)")
    logger.info("="*60 + "\n")
    
    try:
        client = get_cosmos_client()
        
        # Seed all collections (each clears its collection first)
        products_count = await seed_products(client)
        print()  # Blank line
        pricing_count = await seed_pricing(client)
        print()
        stock_count = await seed_stock(client)
        print()
        profiles_count = await seed_user_profiles(client)
        
        # Verify
        await verify_data(client)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Seeding Summary:")
        logger.info(f"  Products: {products_count}")
        logger.info(f"  Pricing: {pricing_count}")
        logger.info(f"  Stock: {stock_count}")
        logger.info(f"  User Profiles: {profiles_count}")
        logger.info("="*60)
        logger.info("\n✅ Demo data seeding complete!")
        logger.info("\n💡 This script is IDEMPOTENT - safe to run multiple times")
        logger.info("\nYou can now:")
        logger.info("  • Run integration tests: uv run pytest test_integration.py -v -s")
        logger.info("  • Start the MCP server: uv run python main.py")
        logger.info("  • Test with the client: uv run python test_client.py")
        
    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
