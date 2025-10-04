# Azure AI Foundry Agent Service in VNet

🔒 **Private, secure conversational product discovery system** using Azure AI Foundry agents, FastAPI backend, React frontend, and Cosmos DB vector search—deployed entirely within an Azure Virtual Network with no public endpoints.

## 🎯 What It Does

A two-agent conversational system that helps users discover products based on their preferences:

1. **Facilitator Agent**: Retrieves user profile (allergies, preferences, hobbies), asks minimal clarifying questions, produces normalized requirements
2. **Product_Finder Agent**: Performs vector similarity search + enrichment (pricing, stock) → returns ranked recommendations with rationale

All agents run inside **Azure AI Foundry Agent Service** and interact with a **FastAPI backend** exposing MCP (Model Context Protocol) tools backed by **Azure Cosmos DB** with vector search.

## 🏗️ Architecture

```
User (via Jump Host Browser)
  ↓
React Frontend (Container Apps, internal ingress)
  ↓
FastAPI Backend (Container Apps, internal ingress)
  ↓
├─ Azure AI Foundry Agent Service (gpt-5, gpt-5-mini, text-embedding-3-large)
├─ Products MCP Server (Container Apps, FastMCP)
└─ Cosmos DB NoSQL + Vector Search (private endpoint)
```

**Security-First Design:**
- ✅ All resources inside VNet (`10.50.0.0/16` + `172.21.0.0/16`)
- ✅ Private endpoints for Cosmos DB, ACR, AI Foundry
- ✅ Azure Firewall Basic (default deny outbound)
- ✅ Azure Bastion + Ubuntu 24.04 jump host for access
- ✅ Managed Identity authentication (no keys)
- ✅ Entra ID user authentication

## 🧩 Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Facilitator Agent** | Azure AI Foundry + Python | Profile retrieval & requirements elicitation |
| **Product_Finder Agent** | Azure AI Foundry + Python | Vector search & recommendation ranking |
| **Products MCP Server** | FastAPI + FastMCP | Tool surface (search, pricing, stock, ranking) |
| **Backend API** | FastAPI (placeholder) | Future REST API for frontend |
| **Frontend** | React + `assistant-ui` | Conversational UI |
| **Database** | Cosmos DB NoSQL + Vector | Products (embeddings), pricing, stock, profiles |
| **Infrastructure** | Terraform (azurerm + azapi) | Networking, compute, AI services |

**Data Collections:**
- `products` – 2048-dim embeddings (text-embedding-3-large), category, tags, attributes
- `pricing` – price, currency, effective dates
- `stock` – quantity, warehouse locations
- `user_profiles` – allergies, preferences, favorite categories

## 🚀 Quick Start

### Prerequisites

- Azure subscription with Owner access
- Azure CLI (`az login`)
- Terraform 1.5+
- Python 3.12+ with `uv` package manager
- VS Code with Remote-SSH extension (for jump host access)

### 1. Deploy Infrastructure

```bash
cd terraform

# Create secrets file
cat > secrets.auto.tfvars <<EOF
subscription_id = "your-subscription-id"
jump_host_admin_password = "ComplexP@ssw0rd!"
jump_host_admin_ssh_key = "ssh-rsa AAAAB3NzaC1yc2E... user@host"  # optional
repo_root = "C:/git/d-ai-froundy-agent-vnet"  # Windows
# repo_root = "/home/user/repos/d-ai-froundy-agent-vnet"  # Linux
EOF

# Initialize and deploy
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

⏱️ **Deployment time:** ~25-30 minutes

**What gets created:**
- Virtual network with 7 subnets (ACA, Foundry, private endpoints, Bastion, jump, firewall)
- Azure Firewall Basic with allow-list rules
- Azure Container Registry (private)
- Azure Container Apps Environment (private, 3 apps with placeholder images)
- Azure Cosmos DB with vector index
- Azure AI Foundry account + GPT-5 family deployments (50 PTU each)
- Azure Bastion Standard + Ubuntu 24.04 jump VM
- Private DNS zones for all services

### 2. Seed Cosmos DB Data

Connect to jump host and populate the database:

```bash
# From your local machine, create SSH tunnel
az network bastion tunnel \
  --name bas-daf-xxxxx \
  --resource-group rg-daf-xxxxx \
  --target-ip-address 172.21.16.4 \
  --resource-port 22 \
  --port 2222

# In another terminal, SSH to jump host
ssh -p 2222 azureuser@localhost

# On jump host
cd /path/to/repo
cd src/tools/products_mcp
uv run python seed_data.py
```

### 3. Build & Deploy MCP Server

The MCP server image needs to be built and pushed to ACR:

```bash
# From your local machine (or jump host)
cd deploy
uv run python build_and_push_mcp.py
```

This script:
1. ✅ Builds container image in ACR (no local Docker needed)
2. ✅ Pushes to ACR as `products-mcp:latest`
3. ✅ Updates Container App with new image
4. ✅ Creates new revision

**Similar process for backend/frontend** (when implemented).

### 4. Connect to Jump Host with VS Code

Configure VS Code Remote-SSH to work through Azure Bastion:

1. Start Bastion tunnel (keep running):
   ```powershell
   # PowerShell
   .\scripts\connect_bastion_tunnel.ps1
   ```

2. Add to `~/.ssh/config`:
   ```
   Host jump-daf-azure
     HostName localhost
     Port 2222
     User azureuser
     StrictHostKeyChecking no
     UserKnownHostsFile /dev/null
   ```

3. VS Code: `F1` → "Remote-SSH: Connect to Host..." → `jump-daf-azure`

Now you can develop directly on the jump host with full Azure access!

### 5. Test MCP Server

From the jump host:

```bash
cd src/tools/products_mcp

# Test deployed MCP server
export MCP_ENDPOINT=https://aca-mcp-daf-xxxxx.internal.swedencentral.azurecontainerapps.io
uv run python test_deployment.py

# Test agent locally
cd ../../agents/facilitator
uv run python main.py
```

## 📊 Configuration Files

Terraform **automatically generates** `.env` files from deployed infrastructure:

| File | Purpose | Generated Variables |
|------|---------|---------------------|
| `deploy/.env` | Build/push scripts | ACR_NAME, RESOURCE_GROUP, BASE_NAME |
| `src/tools/products_mcp/.env` | MCP server config | Cosmos DB endpoint, embeddings config |
| `src/agents/facilitator/.env` | Agent config | AI Foundry project endpoint, model deployment |
| `scripts/connect_bastion_tunnel.ps1` | SSH tunnel | Bastion name, resource group, target IP |

**No manual copying needed!** Run `terraform apply` and all config files are updated.

## 🧪 Testing

### Unit Tests (All Components)

```bash
# MCP Server
cd src/tools/products_mcp
uv run pytest

# Agents
cd src/agents/facilitator
uv run python main.py  # smoke test
```

### Deployment Tests (From Jump Host)

```bash
# End-to-end MCP server test
cd src/tools/products_mcp
export MCP_ENDPOINT=https://aca-mcp-daf-xxxxx.internal.swedencentral.azurecontainerapps.io
uv run python test_deployment.py
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[PRD.md](PRD.md)** | Product requirements & scope |
| **[SolutionDesign.md](SolutionDesign.md)** | Architecture, data models, API contracts |
| **[AGENTS.md](AGENTS.md)** | Development guidelines & collaboration protocols |
| **[ImplementationLog.md](ImplementationLog.md)** | Detailed change history |
| **[CommonErrors.md](CommonErrors.md)** | Troubleshooting guide |
| **[terraform/README.md](terraform/README.md)** | Infrastructure details |
| **[modules/jump/README.md](terraform/modules/jump/README.md)** | Jump host setup & VS Code Remote-SSH |

## 🛠️ Development Workflow

1. **Infrastructure changes:** Edit Terraform → `terraform plan` → review → `terraform apply`
2. **MCP server changes:** Edit code → commit → `cd deploy && uv run python build_and_push_mcp.py`
3. **Agent changes:** Edit code → test locally on jump host → commit
4. **Frontend/Backend changes:** (Coming soon - similar to MCP pattern)

## 🔧 Key Features

### Vector Search
- 2048-dimensional embeddings using `text-embedding-3-large`
- Cosine similarity with filtered search (category, tags)
- Integrated with Cosmos DB vector index

### Ranking Algorithm
```
score = 0.55 × similarity 
      + 0.15 × normalized_popularity
      + 0.15 × price_affinity
      + 0.15 × availability_factor
```

Exclusions: allergens, out-of-stock, price constraints

### Authentication
- **User Auth:** Entra ID (MSAL.js in frontend)
- **Service Auth:** Managed Identity (no keys)
- **Data Plane:** Azure RBAC for Cosmos DB

## 🌐 Networking Details

**Subnets:**
- `snet-aca` (10.50.0.0/23) – Container Apps
- `snet-foundry` (172.21.32.0/24) – AI Foundry network injection
- `snet-pes` (10.50.2.0/24) – Private endpoints
- `snet-bastion` (172.21.0.0/26) – Azure Bastion
- `snet-jumphost` (172.21.16.0/24) – Jump VM
- `snet-firewall` (10.50.255.0/26) – Azure Firewall

**Firewall Allow Rules:**
- Ubuntu package repos (apt, snap)
- Developer tools (Azure CLI, Terraform, GitHub, VS Code)
- Python package managers (pip, PyPI, uv)
- Azure services (Entra ID, Azure Monitor)
- AI services (OpenAI, Microsoft Learn)

## 🎯 What's Next?

- [ ] Implement FastAPI backend with REST endpoints
- [ ] Build React frontend with `assistant-ui`
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Implement frontend-to-backend authentication
- [ ] Add observability dashboards
- [ ] Create user onboarding flow

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Read **[AGENTS.md](AGENTS.md)** for development guidelines
2. Update **[ImplementationLog.md](ImplementationLog.md)** for all changes
3. Test thoroughly on jump host before committing
4. Keep documentation in sync with code

---

**Built with:** Azure AI Foundry • FastAPI • React • Cosmos DB • Terraform • Azure Container Apps
