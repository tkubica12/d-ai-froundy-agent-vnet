# Product finder agent

Recommendation-focused agent that consumes the Facilitator requirements contract and orchestrates vector search, pricing, stock, and ranking tools. It blends cosine similarity with business heuristics (availability, price affinity, popularity) to return a primary match plus rationale-backed alternatives.

Hosted in Azure AI Foundry Agent Service, the agent operates over internal endpoints only. Tool invocations rely on the backend FastAPI service, and outputs follow the standardized response schema defined in the solution design for seamless frontend rendering.