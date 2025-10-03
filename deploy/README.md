# Deploy Scripts

## Azure Container Registry Remote Build

Build and push the Products MCP server Docker image using Azure Container Registry's remote build capability.

### Prerequisites

- Azure CLI installed and logged in (`az login`)
- Access to an Azure Container Registry

### Setup

1. Copy and configure the environment file:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` and set your ACR name:
   ```
   ACR_NAME=your-registry-name
   ```

### Usage

Build and push the MCP server image:

```bash
uv run build_and_push_mcp.py
```

The script will:
- Validate prerequisites (Azure CLI, login status)
- Upload the build context to ACR
- Build the image remotely in Azure (no local Docker required)
- Tag the image as `products-mcp:latest`

The resulting image will be available at: `{ACR_NAME}.azurecr.io/products-mcp:latest`
