resource "azurerm_firewall_policy" "main" {
  name                = "fwpol-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Basic"
  tags                = var.tags
}
