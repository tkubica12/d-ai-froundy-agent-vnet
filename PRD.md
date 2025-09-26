# Product Requirements (PRD)

## What It Is
Internal, network‑isolated conversational product discovery experience composed of two Azure AI Foundry agents (Facilitator & Product_Finder), a Python backend, React UI, and Azure Cosmos DB (vector search). Entire solution runs inside an Azure Virtual Network; no public endpoints are exposed.

## What It Does
1. Authenticated user (Entra ID) interacts with Facilitator agent through React `assistants-ui`.
2. Facilitator retrieves the user profile (allergies, preferences, favorite categories, hobbies) and, if needed, asks minimal clarifying questions.
3. Product_Finder performs vector similarity + rule filtering over product catalog; enriches with pricing and stock; returns the best product plus alternatives with brief rationale.

## Core Functional Scope
- Two agents: profile elicitation + recommendation.
- Data collections: products (with embeddings), pricing, stock, user_profiles.
- Vector search + filtering (allergies, categories, availability).
- Ranking heuristic (similarity + basic business signals).
- Frontend configurable backend URL at container start.

## Security & Isolation Requirements
- All workloads (agents, backend, frontend, Cosmos DB, ACR) reachable only via VNet + private endpoints.
- No public ingress; access for demo via jump host (Bastion + VM) inside the VNet.
- Outbound egress restricted by Azure Firewall Basic (allow only necessary Azure identity / base image endpoints).
- Entra ID for user authentication; Managed Identity for service-to-service (Cosmos, ACR pulls).

## Cloud & Operations
- Provisioned via Terraform (modules: networking, foundry, application, jump, root) using `azurerm` + `azapi`.
- Deployed on Azure Container Apps (frontend + backend) and Azure AI Foundry Agent Service.
- Minimal logging (structured JSON) for traceability of tool calls and recommendations.

## Out of Scope (Initial)
- Advanced ML personalization, analytics dashboards, multi-language UI, SLAs, KPIs, compliance metrics.

