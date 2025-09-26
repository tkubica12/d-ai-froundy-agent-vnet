# Solution Design

## 1. Overview
Private Azure‑hosted conversational product discovery system with two agents (Facilitator, Product_Finder) using Azure AI Foundry Agent Service, Python backend (FastAPI), React `assistants-ui` frontend, and Cosmos DB (vector search). All resources are isolated inside a single VNet (no public ingress) and provisioned by Terraform (`azurerm` + `azapi`).

## 2. High-Level Architecture
```
User (via Jump Host Browser)
   -> ACA Frontend (React, internal ingress)
       -> ACA Backend (FastAPI)
            -> Cosmos DB (products | pricing | stock | user_profiles)
            -> Azure AI Foundry Agent Service (2 agents calling backend MCP tools)
            -> ACR (private) for image pulls
            -> Log Analytics (logs/metrics)
            -> Entra ID (token validation outbound through Firewall allow list)

All endpoints private: PE + Private DNS. Outbound egress controlled by Azure Firewall Basic.
```

## 3. Domain Model & Data Schemas
### 3.1 Collections (Logical JSON Schemas)
`products`:
```json
{
  "id": "string",
  "name": "string",
  "category": "string",
  "tags": ["string"],
  "attributes": {"key": "value"},
  "embedding": [0.0],
  "popularity_score": 0.0,
  "created_utc": "2025-01-01T00:00:00Z",
  "updated_utc": "2025-01-01T00:00:00Z"
}
```
`pricing`:
```json
{
  "id": "string", 
  "product_id": "string",
  "price": 12.34,
  "currency": "USD",
  "effective_from": "2025-01-01T00:00:00Z",
  "effective_to": null
}
```
`stock`:
```json
{
  "id": "string",
  "product_id": "string",
  "quantity_available": 42,
  "warehouse_locations": ["EU-WEST", "US-EAST"],
  "last_updated_utc": "2025-01-01T00:00:00Z"
}
```
`user_profiles`:
```json
{
  "user_id": "<entra_oid>",
  "allergies": ["nuts"],
  "preferences": {"flavor": "spicy", "color": "red"},
  "favorite_categories": ["outdoor"],
  "hobbies": ["hiking"],
  "last_updated_utc": "2025-01-01T00:00:00Z"
}
```

### 3.2 Indexing & Vector
- Vector index on `products.embedding` (cosine). Dimension fixed (e.g. 1536).  
- Secondary indexes on `category`, `tags` for filtered similarity.

## 4. Agents
### 4.1 Facilitator Agent
Purpose: Retrieve profile, fill gaps minimally, output normalized requirements contract.
Requirements Contract (produced JSON):
```json
{
  "must_not_include_allergens": ["nuts"],
  "preferred_categories": ["outdoor"],
  "style_preferences": {"flavor": "spicy"},
  "max_price": 100.0,
  "other_notes": "likes red items"
}
```

### 4.2 Product_Finder Agent
Consumes requirements, performs vector + enrichment, returns recommendation set:
```json
{
  "primary": {"product_id": "abc123", "score": 0.91, "reason": "Matches flavor + category, in stock"},
  "alternatives": [
    {"product_id": "def456", "score": 0.88},
    {"product_id": "ghi789", "score": 0.85}
  ]
}
```

### 4.3 MCP Tool Surface (Logical)
| Tool | Backend Endpoint | Purpose |
|------|------------------|---------|
| get_user_profile | GET /api/profile | Fetch current user profile |
| vector_search_products | POST /api/vector-search | Retrieve candidate products w/ similarity |
| get_pricing | POST /api/pricing | Batch pricing lookup |
| get_stock | POST /api/stock | Batch stock lookup |
| rank_candidates | POST /api/rank | Apply heuristic scoring & filtering |

## 5. API Contracts
All requests authenticated via Bearer JWT (Entra ID access token). Response errors use uniform problem shape:
```json
{ "error": { "code": "string", "message": "string", "details": {} } }
```

### 5.1 GET /healthz
200 OK => `{ "status": "ok" }`

### 5.2 GET /api/profile
Response 200:
```json
{ "user_id": "...", "allergies": [], "preferences": {}, "favorite_categories": [], "hobbies": [] }
```
404 if profile absent (first‑time user) => `{ "error": {"code":"NotFound","message":"profile missing"}}`

### 5.3 POST /api/vector-search
Request:
```json
{ "query_text": "optional string", "embedding": [0.0], "filters": {"category": "outdoor"}, "top_k": 20 }
```
Response:
```json
{ "candidates": [ { "product_id": "p1", "similarity": 0.93 }, { "product_id": "p2", "similarity": 0.89 } ] }
```
Rules: either `embedding` or `query_text` required.

### 5.4 POST /api/pricing
Request:
```json
{ "product_ids": ["p1", "p2"] }
```
Response:
```json
{ "pricing": [ {"product_id": "p1", "price": 19.99, "currency": "USD"} ] }
```

### 5.5 POST /api/stock
Request: `{ "product_ids": ["p1", "p2"] }`
Response:
```json
{ "stock": [ {"product_id": "p1", "quantity_available": 12} ] }
```

### 5.6 POST /api/rank
Request:
```json
{
  "requirements": {"must_not_include_allergens": ["nuts"], "preferred_categories": ["outdoor"]},
  "candidates": [
    {"product_id": "p1", "similarity": 0.92, "price": 25.0, "quantity_available": 5, "popularity_score": 0.7},
    {"product_id": "p2", "similarity": 0.88, "price": 22.0, "quantity_available": 0, "popularity_score": 0.9}
  ]
}
```
Response:
```json
{
  "primary": {"product_id": "p1", "score": 0.91, "reason": "in stock + high similarity"},
  "alternatives": [ {"product_id": "p2", "score": 0.00, "excluded_reason": "out_of_stock"} ]
}
```

## 6. Authentication & Authorization
Flow:
1. MSAL.js obtains Entra ID access token (SPA app registration).
2. Token (audience = backend API app) passed to backend; backend caches JWKS keys.
3. Backend determines user_id (OID claim) and uses it for profile partition key.
4. Managed Identity for backend to Cosmos DB; no keys stored. Frontend never accesses Cosmos directly.
5. Agent Service tool calls propagate user token or use service MI (future variant) restricted by backend checks.

## 7. Networking & Security
Subnets: `snet-aca`, `snet-foundry`, `snet-cosmos-pe`, `snet-acr-pe`, `snet-bastion`, `snet-jumphost`, `snet-firewall`.
Controls:
- Private Endpoints: Cosmos, ACR, Foundry.
- Private DNS Zones: `privatelink.documents.azure.com`, `privatelink.azurecr.io`, AI Foundry domain.
- Azure Firewall Basic: default deny; allow Entra ID, time sync, base image registries if not private.
- ACA internal ingress only; access via jump VM browser.
- All inter-service calls over internal RFC1918 ranges.

## 8. Terraform Structure
```
terraform/
  main.tf            # root orchestrator
  providers.tf
  variables.tf
  outputs.tf
  modules/
    networking/
    foundry/
    application/
    jump/
```
Highlights:
- `networking`: VNet, subnets, firewall, private DNS, routes.
- `foundry`: Agent Service via `azapi_resource`, agents + tool endpoints.
- `application`: ACR, ACA env, backend/frontend apps, Cosmos DB (serverless + vector), identities.
- `jump`: Bastion + VM + NSG.

Example (pseudo) agent service resource:
```hcl
resource "azapi_resource" "agent_service" {
  type      = "Microsoft.AIAgentPlatform/agentServices@2025-01-01-preview"
  name      = var.agent_service_name
  parent_id = azurerm_resource_group.rg.id
  location  = var.location
  body = jsonencode({
    properties = { network = { vnetSubnetId = var.subnet_id } }
  })
}
```

## 9. Build & Deployment
GitHub Actions Workflows:
- `infra.yml`: Terraform fmt/validate/plan/apply (manual approval gate).
- `build-and-deploy.yml`: build & push backend + frontend images (tag: sha + latest) to ACR; update ACA (either Terraform apply or direct CLI revision patch). Optional internal smoke test (self‑hosted runner in VNet).

Backend Docker (conceptual):
```
FROM mcr.microsoft.com/devcontainers/python:3.12
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY . .
ENV PORT=8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Frontend runtime config injection via entrypoint script substituting `__API_BASE_URL__` placeholder.

## 10. Runtime Configuration
| Variable | Component | Description |
|----------|-----------|-------------|
| BACKEND_API_URL | Frontend | Injected into runtime config JSON |
| VECTOR_TOP_K | Backend | Default candidate size (20) |
| MIN_SIMILARITY_THRESHOLD | Backend | Drop low-similarity items |
| COSMOS_DB_NAME | Backend | Logical db separation per env |

## 11. Sequence Flows
Initial Recommendation:
1. User auth (MSAL) -> token.
2. Facilitator starts conversation -> tool `get_user_profile`.
3. If gaps, clarifying Qs; produce requirements JSON.
4. Product_Finder: vector search -> pricing -> stock -> rank.
5. Return primary + alternatives to UI.

## 12. Ranking Logic
Heuristic:
```
score = 0.55*similarity + 0.15*normalized_popularity + 0.15*price_affinity + 0.15*availability_factor
```
Exclusions applied first: allergens, `quantity_available == 0`, disallowed categories.
`price_affinity` = 1 - |price - target_price| / target_price (clamped ≥0) when target provided; else 0.5 baseline.
`availability_factor` = log10(1 + quantity_available)/log10(1 + max_visible_quantity).

## 13. Observability & Ops
Logging: structured JSON (trace_id, user_id hash, tool_name, latency_ms).  
Metrics: `vector_search_ms`, `ranking_ms`, `products_considered`, `recommendation_latency_ms`.  
Alerts: high 5xx %, elevated latency.  
Scaling: ACA autoscale by HTTP RPS or CPU; Cosmos serverless auto RUs (monitor for upgrade).  
Security hardening: ACR image scanning, Dependabot, CodeQL, least-privilege role assignments.

## 14. Assumptions & Open Items
- Vector dimension stable; ingestion validates length.
- Preview API versions for Agent Service may evolve (pin & monitor). 
- Profile creation path (empty profile) returns 404; UI triggers lightweight onboarding (future).

## 15. Summary
This refined design adds explicit data schemas and API contracts, clarifies ranking and sequence flows, and maintains a minimal, private, Terraform-managed Azure architecture aligned with the concise PRD.

---
End of Solution Design.
