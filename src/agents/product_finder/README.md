# Product Finder Agent

Recommendation-focused agent that consumes the Facilitator requirements contract and orchestrates vector search, pricing, stock, and ranking tools. It blends cosine similarity with business heuristics (availability, price affinity, popularity) to return a primary match plus rationale-backed alternatives.

Hosted in Azure AI Foundry Agent Service, the agent operates over internal endpoints only. Tool invocations rely on the backend FastAPI service, and outputs follow the standardized response schema defined in the solution design for seamless frontend rendering.

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
   - `jinja2>=3.1.0` - Template rendering for system prompts

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
4. Create a product finder agent with specialized instructions
5. Start a conversation thread
6. Send a test message: "Can you help me find products for someone with a nut allergy who likes organic food?"
7. Process the agent's response
8. Display the full conversation transcript
9. Clean up by deleting the test agent

## Expected Output

On success, you should see colorful, structured output with emojis:

```
🧪 PRODUCT FINDER AGENT SMOKE TEST
📍 Endpoint: https://your-project.services.ai.azure.com/api/projects/your-id
🤖 Model: gpt-4o

🔐  Authenticating with Azure...
🏗️  Creating product finder agent...
✅  Created agent with ID: asst_xxxxx
💬  Creating conversation thread...
✅  Created thread with ID: thread_xxxxx
📤  Sending test message: 'Can you help me find products...'
✅  Created message with ID: msg_xxxxx
⚙️  Running agent and waiting for response...
✅  Run completed with status: COMPLETED

💬 CONVERSATION TRANSCRIPT

👤 USER: Can you help me find products for someone with a nut allergy...

🤖 ASSISTANT: Yes—I can search products and provide recommendations...

🧹  Cleaning up - deleting agent...
✅  Agent deleted

🎉 SMOKE TEST PASSED! 🎉
The product finder agent is working correctly.
```

## System Prompt

The agent's behavior is defined in `system_prompt.jinja2`, which can be edited without modifying Python code. The prompt defines the agent's role as a product finder specialized in:
- Analyzing user requirements and preferences
- Searching through product catalogs
- Matching products to user needs
- Considering allergies and dietary restrictions
- Providing detailed recommendations with reasoning

## Troubleshooting

### Missing Environment Variables
```
❌ PROJECT_ENDPOINT environment variable is not set
```
**Solution**: Copy `.env.sample` to `.env` and configure your Azure AI Foundry project endpoint.

### Authentication Errors
```
❌ DefaultAzureCredential failed to retrieve a token
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