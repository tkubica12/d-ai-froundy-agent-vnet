# MCP Server with product tools

FastAPI-based MCP implementation that exposes product catalog utilities to the Azure AI Foundry agents. It surfaces endpoints for vector search, pricing, stock, and ranking while enforcing the shared problem-details error contract.

The server talks to Cosmos DB (vector index + transactional data) via managed identity and adheres to the private networking model—only agent service identities inside the VNet can reach it. Logging captures tool latency, response sizes, and correlation IDs for the platform observability story.