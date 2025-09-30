output "bastion_host_id" {
  description = "Resource ID of the Azure Bastion host."
  value       = azurerm_bastion_host.main.id
}

output "jump_host_private_ip" {
  description = "Private IP address assigned to the jump host."
  value       = azurerm_network_interface.jump.ip_configuration[0].private_ip_address
}

output "jump_host_identity_principal_id" {
  description = "Principal ID of the jump host system-assigned managed identity."
  value       = azurerm_windows_virtual_machine.jump.identity[0].principal_id
}
