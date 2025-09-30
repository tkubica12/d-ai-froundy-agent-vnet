output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Name of the resource group that hosts the solution."
}

output "network_virtual_network_id" {
  value       = module.networking.virtual_network_id
  description = "Virtual network identifier."
}

output "cosmos_account_id" {
  value       = module.application.cosmos_account_id
  description = "Cosmos DB account resource ID."
}

output "backend_container_app_fqdn" {
  value       = module.application.backend_container_app_fqdn
  description = "Internal FQDN of the backend container app."
}

output "frontend_container_app_fqdn" {
  value       = module.application.frontend_container_app_fqdn
  description = "Internal FQDN of the frontend container app."
}

output "cognitive_account_id" {
  value       = module.foundry.cognitive_account_id
  description = "Azure AI Foundry account resource ID."
}

output "cognitive_account_endpoint" {
  value       = module.foundry.cognitive_account_endpoint
  description = "Azure AI Foundry account endpoint URI."
}

output "bastion_host_id" {
  value       = module.jump.bastion_host_id
  description = "Azure Bastion host resource ID."
}
