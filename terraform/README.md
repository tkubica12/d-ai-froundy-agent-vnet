# Terraform infrastructure as code

IaC workspace orchestrating the private Azure footprint: virtual network, firewall, private endpoints, Cosmos DB, Container Apps, and Azure AI Foundry agent service. The configuration uses both `azurerm` and `azapi` providers, mirroring the modular structure described in the solution design.

Modules are grouped by capability (networking, foundry, application, jump) to keep plans focused. Pipelines run `terraform fmt`, `validate`, and gated `plan`/`apply`, ensuring every change preserves the locked-down, no-public-ingress posture of the environment.