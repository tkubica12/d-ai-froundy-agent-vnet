locals {
  vnet_cidr      = var.address_space[0]
  subnet_newbits = 6

  subnet_plan = {
    snet-aca = {
      name  = "snet-aca"
      index = 0
      delegations = [{
        name = "aca-delegation"
        service_delegation = {
          name    = "Microsoft.App/environments"
          actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
        }
      }]
    }
    snet-foundry = {
      name  = "snet-foundry"
      index = 1
      delegations = [{
        name = "foundry-agent-delegation"
        service_delegation = {
          name    = "Microsoft.App/environments"
          actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
        }
      }]
    }
    snet-pes = {
      name                              = "snet-pes"
      index                             = 2
      private_endpoint_network_policies = "Disabled"
    }
    snet-bastion = {
      name  = "AzureBastionSubnet"
      index = 3
    }
    snet-jumphost = {
      name  = "snet-jumphost"
      index = 4
    }
    snet-firewall = {
      name  = "AzureFirewallSubnet"
      index = 5
    }
    snet-firewall-mgmt = {
      name  = "AzureFirewallManagementSubnet"
      index = 6
    }
  }

  subnet_definitions = {
    for key, cfg in local.subnet_plan : key => merge(cfg, {
      address_prefixes = [cidrsubnet(local.vnet_cidr, local.subnet_newbits, cfg.index)]
    })
  }
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
  tags                = var.tags
}

resource "azurerm_subnet" "main" {
  for_each = local.subnet_definitions

  name                 = each.value.name
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = each.value.address_prefixes

  private_endpoint_network_policies = try(each.value.private_endpoint_network_policies, "Enabled")
  service_endpoints                 = try(each.value.service_endpoints, null)

  dynamic "delegation" {
    for_each = try(each.value.delegations, [])
    content {
      name = delegation.value.name

      service_delegation {
        name    = delegation.value.service_delegation.name
        actions = delegation.value.service_delegation.actions
      }
    }
  }
}

resource "azurerm_public_ip" "firewall" {
  name                = "pip-fw-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_public_ip" "firewall_management" {
  name                = "pip-fw-mgmt-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_firewall" "main" {
  name                = "fw-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = "AZFW_VNet"
  sku_tier            = "Basic"
  firewall_policy_id  = azurerm_firewall_policy.main.id
  tags                = var.tags

  ip_configuration {
    name                 = "configuration"
    subnet_id            = azurerm_subnet.main["snet-firewall"].id
    public_ip_address_id = azurerm_public_ip.firewall.id
  }

  management_ip_configuration {
    name                 = "management"
    subnet_id            = azurerm_subnet.main["snet-firewall-mgmt"].id
    public_ip_address_id = azurerm_public_ip.firewall_management.id
  }
}

resource "azurerm_route_table" "main" {
  name                = "rt-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  route {
    name                   = "default-to-fw"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = azurerm_firewall.main.ip_configuration[0].private_ip_address
  }
}

locals {
  subnets_requiring_route_table = [
    "snet-aca",
    "snet-foundry",
    "snet-jumphost"
  ]
}

resource "azurerm_subnet_route_table_association" "egress" {
  for_each = { for key in local.subnets_requiring_route_table : key => azurerm_subnet.main[key].id }

  subnet_id      = each.value
  route_table_id = azurerm_route_table.main.id
}

resource "azurerm_private_dns_zone" "this" {
  for_each            = var.private_dns_zone_names
  name                = each.value
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "this" {
  for_each              = var.private_dns_zone_names
  name                  = "vnet-link-${var.base_name}-${each.key}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.this[each.key].name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
  tags                  = var.tags
}
