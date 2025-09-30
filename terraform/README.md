# Terraform infrastructure as code

IaC workspace orchestrating the private Azure footprint: virtual network, firewall, private endpoints, Cosmos DB, Container Apps, and Azure AI Foundry account with GPT-5 deployment. The configuration uses both `azurerm` and `azapi` providers, mirroring the modular structure described in the solution design.

Modules are grouped by capability (networking, foundry, application, jump) to keep plans focused. Pipelines run `terraform fmt`, `validate`, and gated `plan`/`apply`, ensuring every change preserves the locked-down, no-public-ingress posture of the environment.

## Usage

From this directory:

1. `terraform init` – install providers and wire up modules.
2. `terraform fmt -recursive` – enforce canonical formatting.
3. `terraform validate` – static analysis to catch schema issues early.
4. `terraform plan -out=tfplan` – review the proposed graph (set `TF_VAR_jump_host_admin_password`).
5. `terraform apply tfplan` – deploy after approval.
6. `terraform destroy` – tear down the environment when finished.

All commands require an authenticated Azure CLI session with access to subscription `673af34d-6b28-41dc-bc7b-f507418045e6`.