resource "azurerm_public_ip" "bastion" {
  name                = "pip-bastion-${var.base_name}"
  resource_group_name = var.resource_group_name
  location            = var.location
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_bastion_host" "main" {
  name                = "bastion-${var.base_name}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Standard"
  tunneling_enabled   = true
  ip_connect_enabled  = true
  tags                = var.tags

  ip_configuration {
    name                 = "configuration"
    subnet_id            = var.bastion_subnet_id
    public_ip_address_id = azurerm_public_ip.bastion.id
  }
}

resource "azurerm_network_security_group" "jump" {
  name                = "nsg-jump-${var.base_name}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  security_rule {
    name                       = "AllowBastionSSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
    description                = "Allow SSH from Azure Bastion"
  }

  security_rule {
    name                       = "AllowInternalOutbound"
    priority                   = 200
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "VirtualNetwork"
  }
}

resource "azurerm_network_interface" "jump" {
  name                = "nic-jump-${var.base_name}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.jump_subnet_id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_network_interface_security_group_association" "jump" {
  network_interface_id      = azurerm_network_interface.jump.id
  network_security_group_id = azurerm_network_security_group.jump.id
}

resource "azurerm_linux_virtual_machine" "jump" {
  name                            = "vm-jump-${var.base_name}"
  resource_group_name             = var.resource_group_name
  location                        = var.location
  size                            = "Standard_B2s"
  admin_username                  = var.admin_username
  network_interface_ids           = [azurerm_network_interface.jump.id]
  disable_password_authentication = false
  admin_password                  = var.admin_password
  tags                            = var.tags
  computer_name                   = substr("jump${replace(var.base_name, "-", "")}", 0, 15)

  # Configure SSH key if provided (alongside password authentication)
  dynamic "admin_ssh_key" {
    for_each = var.admin_ssh_public_key != "" ? [1] : []
    content {
      username   = var.admin_username
      public_key = var.admin_ssh_public_key
    }
  }

  os_disk {
    name                 = "osdisk-jump-${var.base_name}"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  identity {
    type = "SystemAssigned"
  }

  custom_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
    admin_username = var.admin_username
  }))
}

resource "azurerm_virtual_machine_extension" "aad_ssh_login" {
  name                       = "AADSSHLoginForLinux"
  virtual_machine_id         = azurerm_linux_virtual_machine.jump.id
  publisher                  = "Microsoft.Azure.ActiveDirectory"
  type                       = "AADSSHLoginForLinux"
  type_handler_version       = "1.0"
  auto_upgrade_minor_version = true
  tags                       = var.tags
}
