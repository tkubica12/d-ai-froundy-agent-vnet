locals {
  # Cosmos DB Data Plane RBAC roles
  # https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac
  cosmos_data_contributor_role_id = "00000000-0000-0000-0000-000000000002"  # Built-in Cosmos DB Data Contributor
}

# Grant backend container app identity access to Cosmos DB
resource "azurerm_cosmosdb_sql_role_assignment" "backend" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/${local.cosmos_data_contributor_role_id}"
  principal_id        = azurerm_user_assigned_identity.backend.principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

# Grant jump VM system-assigned identity access to Cosmos DB for testing
resource "azurerm_cosmosdb_sql_role_assignment" "jump_vm" {
  count               = var.jump_vm_principal_id != null ? 1 : 0
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/${local.cosmos_data_contributor_role_id}"
  principal_id        = var.jump_vm_principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

# Note: Frontend does not need direct Cosmos access - it goes through backend API
