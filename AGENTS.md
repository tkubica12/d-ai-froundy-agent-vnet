# Agent Instructions

## Repository Purpose
This project delivers a private Azure AI Foundry agent experience with a FastAPI backend, a React `assistant-ui` frontend, and Azure Cosmos DB vector search, all deployed inside a locked-down virtual network and provisioned through Terraform.

## Required Reading Before Any Task
- `PRD.md` for product requirements.
- `SolutionDesign.md` for architecture, data flows, contracts, and Terraform structure.
- `README.md` for up-to-date run/test instructions per component.

Always review these documents before making changes. If an update to `PRD.md` or `SolutionDesign.md` seems necessary, pause, surface the proposed edits to the user, and proceed only after explicit approval.

## Collaboration & Documentation Protocols
- Record every implementation decision or meaningful change in `ImplementationLog.md` as soon as it happens.
- When an issue is resolved and the fix is confirmed, summarize the root cause and remedy in `CommonErrors.md` (create the entry only after the user confirms it is resolved).
- Keep `README.md` sections for each service updated with concise local run and test steps.
- Do not add helper scripts (deployment, configuration, etc.) unless the user explicitly requests them.
- For architecture-impacting changes or any uncertainty, ask the user before proceeding.

## Python Backend (FastAPI)
- Use Python as the primary language and manage the environment with `uv` plus `pyproject.toml` (no `requirements.txt`).
- Run applications with `uv run` and keep backend services on unique local ports to avoid conflicts.
- Structure code for readability and simplicity; split modules when files become large.
- Use docstrings for all public modules, classes, and functions to describe purpose, parameters, return values, and exceptions.
- Limit comments to clarifying non-obvious logic.
- Employ Pydantic models (stored under `models/`) for request/response validation and serialization.
- Use Python's built-in `logging` module with appropriate log levels.
- Prefer FastAPI for API surfaces and FastMCP when implementing MCP servers.

## Frontend (React)
- Build UI with React and the `assistant-ui` library.
- Keep frontend configuration flexible, including runtime-injected backend URLs.

## Testing Expectations
- Use `pytest` for backend tests and place them under `tests/`.
- Add fast, focused tests for new functionality to speed up troubleshooting.
- Ensure all relevant tests pass (via `uv run pytest` or service-specific commands) before marking work complete.

## Infrastructure & Terraform Guidance
- Provision Azure resources with Terraform using both `azurerm` and `azapi` providers.
- Separate Terraform files by resource groupings (e.g., `networking.tf`, `service_bus.tf`, `rbac.tf`, or `container_app.<component>.tf`). Further split files if a section grows too large.
- Provide smart defaults and rich multiline descriptions for variables, including type hints, constraints, and examples.
- Reserve comments for essential context about unusual resource attributes; omit progress commentary.
- Mixing azurerm with azapi is expected for preview resources—follow the patterns described in `SolutionDesign.md`.

## Troubleshooting Workflow
1. Check `CommonErrors.md` for prior fixes.
2. Consult external references (including web searches) if additional insight is required.
3. Document new fixes in `CommonErrors.md` only after resolution is confirmed.

## Additional Guardrails
- Keep Terraform-managed infrastructure untagged unless tags are required or the user asks for them.
- Always coordinate multiple services to avoid port collisions during local development.
- Treat `AGENTS.md` as living documentation—update it when processes change, but confirm material shifts with the user.
