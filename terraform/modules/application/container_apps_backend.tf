# Backend Container App

resource "azurerm_container_app" "backend" {
  name                         = "aca-backend-${var.base_name}"
  container_app_environment_id = azapi_resource.environment.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  template {
    container {
      name   = "backend"
      image  = local.backend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "COSMOS_DB_ACCOUNT"
        value = azurerm_cosmosdb_account.main.name
      }

      env {
        name  = "COSMOS_DB_NAME"
        value = azurerm_cosmosdb_sql_database.main.name
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8080

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  dynamic "registry" {
    for_each = local.backend_image_uses_acr ? [1] : []
    content {
      server   = local.acr_login_server
      identity = azurerm_user_assigned_identity.backend.id
    }
  }
}
