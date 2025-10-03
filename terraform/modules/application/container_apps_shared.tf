# Shared resources for all Container Apps

locals {
  # Use Microsoft placeholder images for initial deployment
  # After Terraform creates infrastructure, build and push real images with deploy/build_and_push_mcp.py
  # Terraform will ignore image changes after initial deployment (see lifecycle blocks)
  default_backend_image   = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  default_frontend_image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  default_mcp_image       = "mcr.microsoft.com/k8se/quickstart:latest"  # Changed from ACR image
  backend_image           = coalesce(var.backend_image, local.default_backend_image)
  frontend_image          = coalesce(var.frontend_image, local.default_frontend_image)
  mcp_image               = coalesce(var.mcp_image, local.default_mcp_image)
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

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

resource "azapi_resource" "environment" {
  type      = "Microsoft.App/managedEnvironments@2025-02-02-preview"
  name      = "cae-${var.base_name}"
  location  = var.location
  parent_id = data.azurerm_resource_group.main.id
  tags      = var.tags

  body = {
    properties = {
      appLogsConfiguration = {
        destination = "log-analytics"
        logAnalyticsConfiguration = {
          customerId = azurerm_log_analytics_workspace.main.workspace_id
          sharedKey  = azurerm_log_analytics_workspace.main.primary_shared_key
        }
      }
      vnetConfiguration = {
        infrastructureSubnetId = var.subnet_ids["snet-aca"]
        internal               = true
      }
      publicNetworkAccess = "Disabled"
      workloadProfiles = [
        {
          name                = "Consumption"
          workloadProfileType = "Consumption"
        }
      ]
    }
  }

  lifecycle {
    ignore_changes = [
      body.properties.infrastructureResourceGroup
    ]
  }
}
