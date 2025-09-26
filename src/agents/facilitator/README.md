# Facilitator agent

Conversational orchestrator that greets the authenticated user, retrieves their profile via the backend tools, and fills only the minimal gaps needed to produce a requirements contract. The JSON contract captures allergies, preferred categories, budget hints, and any free-form notes that downstream services rely on.

This agent runs inside Azure AI Foundry Agent Service with internal networking only. It exposes the `get_user_profile` tool surface, normalizes responses for Product_Finder, and logs structured telemetry for traceability within the private VNet deployment.