# Products MCP Server Container App
# Provides product search, pricing, stock, and ranking via Model Context Protocol

resource "azurerm_container_app" "mcp" {
  name                         = "aca-mcp-${var.base_name}"
  container_app_environment_id = azapi_resource.environment.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.mcp.id]
  }

  template {
    container {
      name   = "mcp"
      image  = local.mcp_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.mcp.client_id
      }

      env {
        name  = "COSMOS_DB_ENDPOINT"
        value = azurerm_cosmosdb_account.main.endpoint
      }

      env {
        name  = "COSMOS_DB_NAME"
        value = azurerm_cosmosdb_sql_database.main.name
      }

      env {
        name  = "EMBEDDINGS_ENDPOINT"
        value = var.embeddings_endpoint
      }

      env {
        name  = "EMBEDDINGS_DEPLOYMENT"
        value = "text-embedding-3-large"
      }

      env {
        name  = "EMBEDDINGS_DIMENSIONS"
        value = "2048"
      }
    }

    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    external_enabled = false
    target_port      = 8080
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  dynamic "registry" {
    for_each = local.mcp_image_uses_acr ? [1] : []
    content {
      server   = local.acr_login_server
      identity = azurerm_user_assigned_identity.mcp.id
    }
  }
}

# Private endpoint for MCP server access from within the VNet
resource "azurerm_private_endpoint" "mcp" {
  name                = "pep-mcp-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_ids["snet-pes"]
  tags                = var.tags

  private_service_connection {
    name                           = "psc-mcp-${var.base_name}"
    is_manual_connection           = false
    private_connection_resource_id = azapi_resource.environment.id
    subresource_names              = ["managedEnvironments"]
  }

  private_dns_zone_group {
    name                 = "pdz-mcp"
    private_dns_zone_ids = [var.private_dns_zone_ids["aca"]]
  }
}
