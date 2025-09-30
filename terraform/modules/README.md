# Terraform modules

This directory contains the reusable building blocks that align with the solution design:

- `networking/` – virtual network, subnets, Azure Firewall Basic, and private DNS zones that isolate every workload and steer outbound traffic through the firewall.
- `application/` – shared platform resources (Log Analytics, Container Apps Environment, Cosmos DB with vector support, ACR, backend/frontend Container Apps) plus the necessary private endpoints and managed identity bindings.
- `foundry/` – Azure AI Foundry agent service instantiated via `azapi`, with facilitator and product finder agents pre-wired to the backend MCP HTTP tools.
- `jump/` – secure admin access path through Azure Bastion and an internal Linux jump host protected by NSG rules.

Each module exposes focused outputs so the root composition can link subnets, identities, and endpoints without leaking unnecessary internals.
