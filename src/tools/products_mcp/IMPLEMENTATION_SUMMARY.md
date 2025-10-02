# Products MCP Server - Implementation Summary

## Overview

Successfully implemented a complete FastMCP-based Model Context Protocol server for product catalog operations, integrated with Azure Cosmos DB and configured with RBAC authentication for secure, keyless access.

## Components Implemented

### 1. MCP Server (`main.py`)

Five FastMCP tools matching the SolutionDesign.md API contracts:

- **`get_user_profile`**: Retrieves user preferences, allergies, and constraints
- **`vector_search_products`**: Performs cosine similarity search on 1536-dim embeddings
- **`get_pricing`**: Batch pricing lookup for multiple products
- **`get_stock`**: Real-time inventory checking
- **`rank_candidates_tool`**: Heuristic-based scoring and recommendation ranking

All tools return standardized error responses using the ErrorResponse/ErrorDetail pattern.

### 2. Data Models (`models.py`)

Pydantic models for request/response validation:
- User profiles with allergies, preferences, hobbies
- Vector search requests with embedding/query_text alternatives
- Pricing and stock batch operations
- Requirements contracts from Facilitator agent
- Enriched candidate products with pricing/stock/popularity
- Ranked product results with scores and reasoning

### 3. Cosmos DB Client (`cosmos_client.py`)

Type-safe Azure Cosmos DB wrapper:
- **Authentication**: DefaultAzureCredential (Managed Identity in Azure, Azure CLI locally)
- **Vector Search**: Native Cosmos DB vector queries with HNSW index
- **Batch Operations**: Efficient multi-product pricing and stock lookups
- **Collections**: products, pricing, stock, user_profiles
- **Error Handling**: CosmosResourceNotFoundError handling for 404s

### 4. Ranking Algorithm (`ranking.py`)

Weighted heuristic scoring:
```
score = 0.55 × similarity 
      + 0.15 × normalized_popularity
      + 0.15 × price_affinity
      + 0.15 × availability_factor
```

Exclusion rules applied first:
- Out of stock (quantity_available == 0)
- Exceeds max_price from requirements
- Contains allergens from user profile

Logarithmic availability scaling prevents large stock quantities from dominating.

### 5. Configuration (`config.py`)

Pydantic settings with .env file support:
- Cosmos DB endpoint and database name
- Optional key (uses Managed Identity if omitted)
- Vector search parameters (top_k, similarity threshold)
- Ranking weight distribution
- Structured logging configuration

### 6. Testing Utility (`test_client.py`)

FastMCP client with two modes:
- **In-memory transport**: Fast testing without subprocess overhead
- **External server**: Stdio transport for integration testing

Includes mock data for all five tools with realistic product scenarios.

### 7. Unit Tests (`test_models.py`)

Seven test cases covering:
- Settings loading and validation
- Pydantic model structure and constraints
- Ranking exclusion logic (allergens, price, stock)
- Score calculation and primary/alternative selection

All tests pass ✓

## Terraform RBAC Configuration

### New Files

**`terraform/modules/application/rbac.tf`**:
- Cosmos DB Data Contributor role assignments
- Backend container app user-assigned identity → Cosmos DB
- Jump VM system-assigned identity → Cosmos DB (conditional, for testing)
- Uses built-in role ID: `00000000-0000-0000-0000-000000000002`

### Updated Files

**`terraform/modules/application/variables.tf`**:
- Added `jump_vm_principal_id` parameter (optional)
- Rich description with usage context

**`terraform/main.tf`**:
- Wired `module.jump.jump_host_identity_principal_id` to application module
- Enables testing from jump host with Managed Identity

### RBAC Summary

| Identity | Resource | Role | Purpose |
|----------|----------|------|---------|
| Backend Container App (User-Assigned) | Cosmos DB | Data Contributor | Production MCP server operations |
| Jump VM (System-Assigned) | Cosmos DB | Data Contributor | Testing from jump host |
| Frontend Container App | - | - | No direct Cosmos access (uses backend API) |

All authentication uses Azure RBAC - **no connection strings or keys in production**.

## Dependencies

Updated `pyproject.toml`:
```toml
dependencies = [
    "fastmcp>=2.4.0",           # MCP protocol implementation
    "azure-cosmos>=4.8.0",      # Cosmos DB SDK with vector search
    "azure-identity>=1.19.0",   # DefaultAzureCredential
    "python-dotenv>=1.0.0",     # .env file loading
    "pydantic>=2.0.0",          # Request/response validation
    "pydantic-settings>=2.0.0", # Settings management
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

## File Structure

```
src/tools/products_mcp/
├── .env                    # Local config (gitignored)
├── .env.sample            # Template with defaults
├── .gitignore             # Python, IDE, OS artifacts
├── config.py              # Pydantic settings
├── cosmos_client.py       # Azure Cosmos DB client
├── main.py                # FastMCP server with 5 tools
├── models.py              # Pydantic request/response models
├── pyproject.toml         # Dependencies and metadata
├── ranking.py             # Heuristic scoring algorithm
├── README.md              # Comprehensive documentation
├── test_client.py         # FastMCP client testing utility
└── test_models.py         # Unit tests (7 tests, all pass)
```

## Local Testing

### Prerequisites
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Log in to Azure (for DefaultAzureCredential)
az login
```

### Setup
```bash
cd src/tools/products_mcp

# Install dependencies
uv sync --extra dev

# Configure environment
cp .env.sample .env
# Edit .env with your Cosmos DB endpoint

# Run unit tests
uv run pytest -v

# Test with mock data (in-memory)
uv run python test_client.py

# Test with external server process
uv run python test_client.py --external
```

### Expected Output

```
=== Starting MCP Server Tests ===

Test 1: Ping server
✓ Server is responsive

Test 2: List available tools
Available tools: 5
  - get_user_profile: Retrieve user profile by user_id
  - vector_search_products: Perform vector similarity search...
  - get_pricing: Retrieve current pricing...
  - get_stock: Retrieve current stock levels...
  - rank_candidates_tool: Rank product candidates...

Test 3: Get user profile
Result: {'error': {'code': 'NotFound', 'message': '...'}}

[... additional tool tests ...]

=== All Tests Complete ===
```

## Azure Deployment

### Container Image Build

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY . .
ENV PORT=8080
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Variables (Container App)

```bash
COSMOS_DB_ENDPOINT=https://cosmos-<name>.documents.azure.com:443/
COSMOS_DB_NAME=appdb
# COSMOS_DB_KEY intentionally omitted - uses Managed Identity
VECTOR_TOP_K=20
MIN_SIMILARITY_THRESHOLD=0.5
LOG_LEVEL=INFO
```

### Terraform Apply

```bash
cd terraform

# Validate configuration
terraform validate  # ✓ Success!

# Preview changes
terraform plan -out=tfplan

# Apply RBAC configuration
terraform apply tfplan
```

## Testing from Jump Host

```bash
# Connect via Bastion
az network bastion ssh \
  --name bastion-<name> \
  --resource-group rg-<name> \
  --target-resource-id <vm-id> \
  --auth-type AAD

# On jump host
cd /workspace/src/tools/products_mcp
uv run python test_client.py
```

The jump VM's system-assigned identity has Cosmos DB access for testing.

## Integration with Azure AI Foundry Agents

### Agent Tool Configuration

Agents declare MCP tools in their configuration:

```json
{
  "name": "product_finder",
  "tools": [
    {
      "type": "mcp",
      "mcp_server": "products-mcp",
      "tool_name": "vector_search_products"
    },
    {
      "type": "mcp", 
      "mcp_server": "products-mcp",
      "tool_name": "get_pricing"
    }
    // ... additional tools
  ]
}
```

### Typical Agent Flow

1. **Facilitator Agent**:
   - Calls `get_user_profile` to retrieve constraints
   - Fills gaps with clarifying questions
   - Produces Requirements contract

2. **Product_Finder Agent**:
   - Calls `vector_search_products` with user embedding
   - Calls `get_pricing` for candidate products
   - Calls `get_stock` for availability
   - Calls `rank_candidates_tool` with enriched data
   - Returns primary recommendation + alternatives

## Observability

Structured logging with correlation:
```python
logger.info(
    f"vector_search_products called with top_k={top_k}",
    extra={"tool": "vector_search", "params": {"top_k": top_k}}
)
```

Captured metrics:
- Tool invocation counts
- Query execution times
- Result set sizes
- Error rates and types

## Security Posture

✅ **No secrets in code**: All auth via Managed Identity  
✅ **Private networking**: Internal-only endpoints via VNet  
✅ **RBAC everywhere**: Least-privilege data plane access  
✅ **Input validation**: Pydantic models enforce schema  
✅ **Error sanitization**: No sensitive data in error messages  

## Known Limitations

1. **Embedding Generation**: MCP server expects pre-computed embeddings; agents must embed query_text externally
2. **Single Region**: Cosmos DB geo-replication not configured
3. **Rate Limiting**: No throttling on tool calls (rely on ACA scaling)
4. **Allergen Detection**: Simplistic tag matching; production needs product attribute enrichment

## Next Steps

1. **Populate Cosmos DB**: Add seed data for products, pricing, stock, user_profiles
2. **Deploy Container Image**: Build and push to ACR, update Terraform `backend_image` variable
3. **Configure Agents**: Wire MCP server endpoint into Facilitator and Product_Finder agent configs
4. **End-to-End Testing**: Test full conversation flow from frontend through agents to MCP tools
5. **Monitoring Setup**: Configure Log Analytics queries and alerts for tool latency/errors

## References

- **Solution Design**: `/SolutionDesign.md` (API contracts, data schemas)
- **FastMCP Docs**: https://gofastmcp.com/
- **Cosmos DB Vector Search**: https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search
- **Azure Identity**: https://learn.microsoft.com/en-us/python/api/azure-identity/
- **Model Context Protocol**: https://modelcontextprotocol.io/

---

**Implementation Date**: 2025-10-02  
**Status**: ✅ Complete - All tests passing, Terraform validated  
**Recorded in**: `ImplementationLog.md`
