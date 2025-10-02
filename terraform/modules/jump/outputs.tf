output "bastion_host_id" {
  description = "Resource ID of the Azure Bastion host."
  value       = azurerm_bastion_host.main.id
}

output "bastion_host_name" {
  description = "Name of the Azure Bastion host."
  value       = azurerm_bastion_host.main.name
}

output "jump_host_id" {
  description = "Resource ID of the jump host VM."
  value       = azurerm_linux_virtual_machine.jump.id
}

output "jump_host_name" {
  description = "Name of the jump host VM."
  value       = azurerm_linux_virtual_machine.jump.name
}

output "jump_host_private_ip" {
  description = "Private IP address assigned to the jump host."
  value       = azurerm_network_interface.jump.ip_configuration[0].private_ip_address
}

output "jump_host_identity_principal_id" {
  description = "Principal ID of the jump host system-assigned managed identity."
  value       = azurerm_linux_virtual_machine.jump.identity[0].principal_id
}

output "ssh_command" {
  description = "Command to SSH to the jump host via Azure Bastion."
  value       = "az network bastion ssh --name ${azurerm_bastion_host.main.name} --resource-group ${var.resource_group_name} --target-resource-id ${azurerm_linux_virtual_machine.jump.id} --auth-type AAD"
}

output "tunnel_command_example" {
  description = "Example command to create SSH tunnel via Azure Bastion (replace ports as needed)."
  value       = "az network bastion tunnel --name ${azurerm_bastion_host.main.name} --resource-group ${var.resource_group_name} --target-ip-address ${azurerm_network_interface.jump.ip_configuration[0].private_ip_address} --resource-port 22 --port 2222"
}
