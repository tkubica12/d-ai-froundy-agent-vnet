locals {
  default_backend_image   = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  default_frontend_image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  backend_image           = coalesce(var.backend_image, local.default_backend_image)
  frontend_image          = coalesce(var.frontend_image, local.default_frontend_image)
  acr_login_server        = azurerm_container_registry.main.login_server
  backend_image_uses_acr  = startswith(local.backend_image, "${local.acr_login_server}/")
  frontend_image_uses_acr = startswith(local.frontend_image, "${local.acr_login_server}/")
}

resource "azurerm_user_assigned_identity" "backend" {
  name                = "id-backend-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "frontend" {
  name                = "id-frontend-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_container_app_environment" "main" {
  name                           = "cae-${var.base_name}"
  location                       = var.location
  resource_group_name            = var.resource_group_name
  infrastructure_subnet_id       = var.subnet_ids["snet-aca"]
  internal_load_balancer_enabled = true
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.main.id
  tags                           = var.tags

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }

  lifecycle {
    ignore_changes = [
      infrastructure_resource_group_name
    ]
  }
}

resource "azurerm_container_app" "backend" {
  name                         = "aca-backend-${var.base_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
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
    external_enabled = false
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

resource "azurerm_container_app" "frontend" {
  name                         = "aca-frontend-${var.base_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
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
    external_enabled = false
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
