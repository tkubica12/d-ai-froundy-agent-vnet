output "cosmos_account_id" {
  description = "Resource ID of the Cosmos DB account."
  value       = azurerm_cosmosdb_account.main.id
}

output "cosmos_database_name" {
  description = "Primary database name used by the application."
  value       = azurerm_cosmosdb_sql_database.main.name
}

output "container_registry_login_server" {
  description = "ACR login server for container pulls."
  value       = azurerm_container_registry.main.login_server
}

output "backend_container_app_fqdn" {
  description = "Internal FQDN of the backend container app."
  value       = azurerm_container_app.backend.latest_revision_fqdn
}

output "frontend_container_app_fqdn" {
  description = "Internal FQDN of the frontend container app."
  value       = azurerm_container_app.frontend.latest_revision_fqdn
}

output "mcp_container_app_fqdn" {
  description = "Internal FQDN of the MCP server container app."
  value       = azurerm_container_app.mcp.latest_revision_fqdn
}

output "backend_managed_identity_id" {
  description = "Resource ID of the backend user-assigned identity."
  value       = azurerm_user_assigned_identity.backend.id
}

output "frontend_managed_identity_id" {
  description = "Resource ID of the frontend user-assigned identity."
  value       = azurerm_user_assigned_identity.frontend.id
}

output "mcp_managed_identity_id" {
  description = "Resource ID of the MCP server user-assigned identity."
  value       = azurerm_user_assigned_identity.mcp.id
}

output "mcp_managed_identity_principal_id" {
  description = "Principal ID of the MCP server user-assigned identity for RBAC assignments."
  value       = azurerm_user_assigned_identity.mcp.principal_id
}
