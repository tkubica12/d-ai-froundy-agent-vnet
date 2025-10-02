# Products MCP Server

FastMCP-based Model Context Protocol server that exposes product catalog utilities to Azure AI Foundry agents. Provides vector search, pricing, stock, and ranking tools backed by Azure Cosmos DB with RBAC authentication.

## Features

- **Vector Search**: Cosine similarity search on product embeddings (1536 dimensions)
- **Pricing Lookup**: Batch pricing retrieval for multiple products
- **Stock Availability**: Real-time inventory checking
- **Intelligent Ranking**: Heuristic-based product recommendation scoring
- **Managed Identity Auth**: Uses Azure DefaultAzureCredential (no keys in production)
- **Structured Logging**: JSON-formatted logs with correlation IDs

## Architecture

The server implements the MCP (Model Context Protocol) specification using FastMCP and exposes five tools:

1. `get_user_profile` - Retrieve user preferences and constraints
2. `vector_search_products` - Find similar products using embeddings
3. `get_pricing` - Fetch current pricing for products
4. `get_stock` - Check inventory availability
5. `rank_candidates_tool` - Score and rank product recommendations

All tools follow the API contracts defined in `SolutionDesign.md`.

## Prerequisites

- Python 3.12+
- `uv` package manager
- Azure Cosmos DB with:
  - NoSQL API with vector search enabled
  - Collections: `products`, `pricing`, `stock`, `user_profiles`
  - RBAC role assignment (Cosmos DB Data Contributor)

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.sample .env
   # Edit .env with your Cosmos DB endpoint
   ```

3. **Environment variables**:
   - `COSMOS_DB_ENDPOINT` - Cosmos DB account endpoint (required)
   - `COSMOS_DB_NAME` - Database name (default: `appdb`)
   - `COSMOS_DB_KEY` - Optional key for local dev (omit to use Managed Identity)
   - `VECTOR_TOP_K` - Default candidate count (default: 20)
   - `MIN_SIMILARITY_THRESHOLD` - Minimum score cutoff (default: 0.5)

## Running Locally

### Development Mode (with Azure CLI authentication)

Ensure you're logged in with Azure CLI and have appropriate permissions:

```bash
az login
uv run python main.py
```

The server will use your Azure CLI credentials via `DefaultAzureCredential`.

### Testing with Mock Data

Run the test client to verify all tools:

```bash
# In-memory testing (fast, no network calls)
uv run python test_client.py

# Test with external server process
uv run python test_client.py --external
```

## Deployment

### Azure Container Apps

The server is designed to run in Azure Container Apps with:
- User-assigned managed identity
- Private networking (internal ingress only)
- Environment variables injected from Terraform

Terraform automatically grants the backend container app identity access to Cosmos DB via RBAC.

### Testing from Jump Host

When deployed, you can test the MCP server from the jump VM:

```bash
# SSH to jump host via Bastion
az network bastion ssh --name <bastion-name> --resource-group <rg> --target-resource-id <vm-id> --auth-type AAD

# On jump host, clone repo and test
cd /path/to/repo/src/tools/products_mcp
uv run python test_client.py
```

The jump VM has Managed Identity access to Cosmos DB for testing purposes.

## API Contracts

All tools follow the standardized error format:

```json
{
  "error": {
    "code": "ErrorCode",
    "message": "Human-readable message",
    "details": {}
  }
}
```

See `models.py` for complete request/response schemas.

## Ranking Algorithm

The ranking tool uses weighted heuristics:

```
score = 0.55 × similarity 
      + 0.15 × normalized_popularity
      + 0.15 × price_affinity
      + 0.15 × availability_factor
```

Exclusions applied first:
- Out of stock items
- Exceeds max price
- Contains allergens from user profile

See `ranking.py` for implementation details.

## Development

### Running Tests

```bash
uv run pytest
```

### Code Structure

```
products_mcp/
├── main.py           # FastMCP server with tool definitions
├── config.py         # Settings from environment/dotenv
├── models.py         # Pydantic request/response models
├── cosmos_client.py  # Azure Cosmos DB client wrapper
├── ranking.py        # Product ranking logic
└── test_client.py    # FastMCP client for testing
```

### Adding New Tools

1. Define request/response models in `models.py`
2. Add database methods to `cosmos_client.py` if needed
3. Implement tool in `main.py` using `@mcp.tool()` decorator
4. Add test case in `test_client.py`

## Observability

Structured logging captures:
- Tool invocations with parameters
- Query execution times
- Result counts and scores
- Error stack traces

Configure log level via `LOG_LEVEL` environment variable.

## Security

- **No secrets in code**: Uses Managed Identity in Azure
- **Private networking**: Internal-only endpoints via VNet
- **RBAC**: Least-privilege data plane access
- **Input validation**: Pydantic models enforce schema

## Troubleshooting

### Authentication Errors

If you see `DefaultAzureCredential failed to retrieve a token`:
- Ensure you're logged in: `az login`
- Check RBAC assignment on Cosmos DB
- Verify Managed Identity is assigned to the container app

### Connection Errors

- Verify `COSMOS_DB_ENDPOINT` is correct
- Check private endpoint and DNS resolution
- Ensure firewall rules allow your source

### Empty Search Results

- Confirm products collection has data with embeddings
- Check vector index is created (see `cosmos.tf`)
- Verify embedding dimensions match (1536)

## References

- [FastMCP Documentation](https://gofastmcp.com/)
- [Azure Cosmos DB Vector Search](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Solution Design](../../../SolutionDesign.md)
