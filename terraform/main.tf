data "azurerm_client_config" "current" {}

resource "random_string" "main" {
  length  = 4
  special = false
  upper   = false
  numeric = false
  lower   = true
}

locals {
  base_name        = "${replace(var.prefix, "_", "-")}-${random_string.main.result}"
  base_name_nodash = replace(local.base_name, "-", "")
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.base_name}"
  location = var.location
  tags     = var.tags
}

module "networking" {
  source = "./modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  base_name           = local.base_name
  tags                = var.tags
}

module "application" {
  source = "./modules/application"

  resource_group_name  = azurerm_resource_group.main.name
  location             = var.location
  base_name            = local.base_name
  base_name_nodash     = local.base_name_nodash
  tags                 = var.tags
  subnet_ids           = module.networking.subnet_ids
  private_dns_zone_ids = module.networking.private_dns_zone_ids
  backend_image        = var.backend_image
  frontend_image       = var.frontend_image
}

module "foundry" {
  source = "./modules/foundry"

  resource_group_name             = azurerm_resource_group.main.name
  resource_group_id               = azurerm_resource_group.main.id
  location                        = var.location
  base_name                       = local.base_name
  tags                            = var.tags
  agent_subnet_id                 = module.networking.subnet_ids["snet-foundry"]
  private_endpoint_subnet_id      = module.networking.subnet_ids["snet-pes"]
  private_dns_zone_ids            = module.networking.private_dns_zone_ids
  jump_host_identity_principal_id = module.jump.jump_host_identity_principal_id
}

module "jump" {
  source = "./modules/jump"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  base_name           = local.base_name
  tags                = var.tags
  bastion_subnet_id   = module.networking.subnet_ids["snet-bastion"]
  jump_subnet_id      = module.networking.subnet_ids["snet-jumphost"]
  admin_username      = var.jump_host_admin_username
  admin_password      = var.jump_host_admin_password
}
