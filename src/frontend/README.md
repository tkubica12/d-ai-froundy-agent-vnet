# Frontend chat UI

React single-page application built with `assistant-ui` to host the Facilitator conversation inside the secured Azure Container Apps environment. It authenticates users with MSAL.js, forwards Entra ID access tokens to the backend, and renders agent messages with streaming updates.

Runtime configuration (such as the internal backend URL) is injected at container start, enabling the same image to run across environments. Observability hooks forward structured logs to the platform, and no direct data access occurs—everything flows through the backend FastAPI APIs.