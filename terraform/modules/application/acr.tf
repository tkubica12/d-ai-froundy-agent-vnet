resource "azurerm_container_registry" "main" {
  name                = lower(substr("acr${var.base_name_nodash}", 0, 50))
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Premium"
  admin_enabled       = false
  tags                = var.tags
}

resource "azurerm_private_endpoint" "acr" {
  name                = "pep-acr-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_ids["snet-pes"]
  tags                = var.tags

  private_service_connection {
    name                           = "psc-acr-${var.base_name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_container_registry.main.id
    subresource_names              = ["registry"]
  }

  private_dns_zone_group {
    name                 = "pdz-acr"
    private_dns_zone_ids = [var.private_dns_zone_ids["acr"]]
  }
}

resource "azurerm_role_assignment" "backend_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

resource "azurerm_role_assignment" "frontend_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.frontend.principal_id
}

resource "azapi_resource_action" "import_backend_image" {
  type        = "Microsoft.ContainerRegistry/registries@2023-01-01-preview"
  resource_id = azurerm_container_registry.main.id
  action      = "importImage"
  method      = "POST"

  body = {
    source = {
      registryUri = "mcr.microsoft.com"
      sourceImage = "azuredocs/containerapps-helloworld:latest"
    }
    targetTags = ["samples/backend:latest"]
    mode       = "Force"
  }

  depends_on = [azurerm_container_registry.main]
}

resource "azapi_resource_action" "import_frontend_image" {
  type        = "Microsoft.ContainerRegistry/registries@2023-01-01-preview"
  resource_id = azurerm_container_registry.main.id
  action      = "importImage"
  method      = "POST"

  body = {
    source = {
      registryUri = "mcr.microsoft.com"
      sourceImage = "azuredocs/containerapps-helloworld:latest"
    }
    targetTags = ["samples/frontend:latest"]
    mode       = "Force"
  }

  depends_on = [azurerm_container_registry.main]
}
