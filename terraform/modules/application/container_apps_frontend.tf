# Frontend Container App

resource "azurerm_container_app" "frontend" {
  name                         = "aca-frontend-${var.base_name}"
  container_app_environment_id = azapi_resource.environment.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.frontend.id]
  }

  template {
    container {
      name   = "frontend"
      image  = local.frontend_image
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "BACKEND_API_URL"
        value = local.backend_internal_url
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  dynamic "registry" {
    for_each = local.frontend_image_uses_acr ? [1] : []
    content {
      server   = local.acr_login_server
      identity = azurerm_user_assigned_identity.frontend.id
    }
  }
}
