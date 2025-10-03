# Shared resources for all Container Apps

locals {
  default_backend_image   = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  default_frontend_image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  backend_image           = coalesce(var.backend_image, local.default_backend_image)
  frontend_image          = coalesce(var.frontend_image, local.default_frontend_image)
  mcp_image               = coalesce(var.mcp_image, "${azurerm_container_registry.main.login_server}/products-mcp:latest")
  acr_login_server        = azurerm_container_registry.main.login_server
  backend_image_uses_acr  = startswith(local.backend_image, "${local.acr_login_server}/")
  frontend_image_uses_acr = startswith(local.frontend_image, "${local.acr_login_server}/")
  mcp_image_uses_acr      = startswith(local.mcp_image, "${local.acr_login_server}/")
  backend_internal_url    = "https://${azurerm_container_app.backend.latest_revision_fqdn}"
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

resource "azurerm_user_assigned_identity" "mcp" {
  name                = "id-mcp-${var.base_name}"
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
