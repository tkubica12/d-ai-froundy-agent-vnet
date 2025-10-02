# Custom Cosmos DB Data Plane RBAC Role Definition
resource "azurerm_cosmosdb_sql_role_definition" "data_contributor" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  name                = "custom-data-contributor-${var.base_name}"
  type                = "CustomRole"
  assignable_scopes   = [azurerm_cosmosdb_account.main.id]

  permissions {
    data_actions = [
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*"
    ]
  }
}

locals {
  # Enable jump VM access only if principal_id is explicitly provided (not empty string)
  enable_jump_vm_access = var.jump_vm_principal_id != ""
}

# Grant backend container app identity access to Cosmos DB
resource "azurerm_cosmosdb_sql_role_assignment" "backend" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = azurerm_cosmosdb_sql_role_definition.data_contributor.id
  principal_id        = azurerm_user_assigned_identity.backend.principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

# Grant jump VM system-assigned identity access to Cosmos DB for testing
# Only created when jump_vm_principal_id is explicitly provided
resource "azurerm_cosmosdb_sql_role_assignment" "jump_vm" {
  count               = local.enable_jump_vm_access ? 1 : 0
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = azurerm_cosmosdb_sql_role_definition.data_contributor.id
  principal_id        = var.jump_vm_principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

