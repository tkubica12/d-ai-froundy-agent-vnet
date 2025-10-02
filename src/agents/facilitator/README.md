# Facilitator agent

Conversational orchestrator that greets the authenticated user, retrieves their profile via the backend tools, and fills only the minimal gaps needed to produce a requirements contract. The JSON contract captures allergies, preferred categories, budget hints, and any free-form notes that downstream services rely on.

This agent runs inside Azure AI Foundry Agent Service with internal networking only. It exposes the `get_user_profile` tool surface, normalizes responses for Product_Finder, and logs structured telemetry for traceability within the private VNet deployment.

## Prerequisites

- Python 3.12+
- `uv` package manager
- Azure CLI (for authentication)
- Azure AI Foundry project with deployed model

## Setup

1. **Install dependencies** (handled automatically by `uv`):
   - `azure-ai-projects>=1.0.0b6` - Azure AI Foundry Agent SDK
   - `azure-identity>=1.19.0` - Azure authentication
   - `python-dotenv>=1.0.1` - Environment variable management

2. **Configure environment variables**:
   ```bash
   cp .env.sample .env
   ```

3. **Edit `.env`** with your Azure AI Foundry project details:
   - `PROJECT_ENDPOINT`: Your Azure AI Foundry project endpoint
     - Format: `https://<project-name>.services.ai.azure.com/api/projects/<project-id>`
     - Find in Azure Portal → AI Foundry project → Overview → Project endpoint
   - `MODEL_DEPLOYMENT_NAME`: The model deployment name (e.g., `gpt-4o`, `gpt-4o-mini`)
     - Find in Azure Portal → AI Foundry project → Deployments

4. **Authenticate with Azure**:
   ```bash
   az login
   ```
   The script uses `DefaultAzureCredential` which automatically tries:
   - Environment variables (service principal)
   - Managed Identity (when running in Azure)
   - Azure CLI credentials (for local development)
   - VS Code credentials
   - Azure PowerShell credentials

## Running the Smoke Test

Run the basic smoke test to verify agent connectivity:

```bash
uv run python main.py
```

The smoke test will:
1. Load environment configuration from `.env`
2. Authenticate with Azure using `DefaultAzureCredential`
3. Connect to Azure AI Foundry Agent Service
4. Create a facilitator agent with basic instructions
5. Start a conversation thread
6. Send a test message: "Hello! Can you help me find products?"
7. Process the agent's response
8. Display the full conversation transcript
9. Clean up by deleting the test agent

## Expected Output

On success, you should see output similar to:

```
INFO - Starting facilitator agent smoke test...
INFO - Project endpoint: https://your-project.services.ai.azure.com/api/projects/your-id
INFO - Model deployment: gpt-4o
INFO - Authenticating with Azure using DefaultAzureCredential...
INFO - ✓ Created agent with ID: asst_xxxxx
INFO - ✓ Created thread with ID: thread_xxxxx
INFO - ✓ Created message with ID: msg_xxxxx
INFO - ✓ Run completed with status: completed
INFO - 
============================================================
CONVERSATION TRANSCRIPT
============================================================

USER: Hello! Can you help me find products?

AGENT: Hello! Yes, I'd be happy to help you find products...

============================================================

INFO - ✓ Deleted agent
INFO - 🎉 SMOKE TEST PASSED! 🎉
INFO - The facilitator agent is working correctly.
```

## Troubleshooting

### Missing Environment Variables
```
ERROR - PROJECT_ENDPOINT environment variable is not set
```
**Solution**: Copy `.env.sample` to `.env` and configure your Azure AI Foundry project endpoint.

### Authentication Errors
```
ERROR - DefaultAzureCredential failed to retrieve a token
```
**Solution**: Run `az login` to authenticate with Azure CLI.

### DNS Resolution Errors
```
Failed to resolve '<endpoint>.services.ai.azure.com'
```
**Solution**: Verify your `PROJECT_ENDPOINT` is correct and matches your Azure AI Foundry project.

### Model Not Found
```
The model deployment 'xxx' was not found
```
**Solution**: Verify `MODEL_DEPLOYMENT_NAME` matches an actual deployment in your Azure AI Foundry project.