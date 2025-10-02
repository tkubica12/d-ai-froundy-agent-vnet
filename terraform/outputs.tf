output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Name of the resource group that hosts the solution."
}

output "network_virtual_network_id" {
  value       = module.networking.virtual_network_id
  description = "Virtual network identifier."
}

output "cosmos_account_id" {
  value       = module.application.cosmos_account_id
  description = "Cosmos DB account resource ID."
}

output "backend_container_app_fqdn" {
  value       = module.application.backend_container_app_fqdn
  description = "Internal FQDN of the backend container app."
}

output "frontend_container_app_fqdn" {
  value       = module.application.frontend_container_app_fqdn
  description = "Internal FQDN of the frontend container app."
}

output "cognitive_account_id" {
  value       = module.foundry.cognitive_account_id
  description = "Azure AI Foundry account resource ID."
}

output "cognitive_account_endpoint" {
  value       = module.foundry.cognitive_account_endpoint
  description = "Azure AI Foundry account endpoint URI."
}

output "bastion_host_id" {
  value       = module.jump.bastion_host_id
  description = "Azure Bastion host resource ID."
}

output "ssh_to_jump_host" {
  value       = module.jump.ssh_command
  description = "Command to SSH to the jump host via Azure Bastion using Azure AD authentication."
}

output "ssh_tunnel_example" {
  value       = module.jump.tunnel_command_example
  description = "Example command to create SSH tunnel via Azure Bastion for port forwarding."
}

output "jump_host_setup_instructions" {
  value       = <<-EOT
    
    === Jump Host Access Instructions ===
    
    1. Install Azure CLI and SSH extension:
       az extension add --name ssh
    
    2. Connect via Azure Bastion (direct):
       ${module.jump.ssh_command}
    
    3. For VS Code Remote SSH, add to ~/.ssh/config:
       Host azure-jump
           HostName ${module.jump.jump_host_private_ip}
           User ${var.jump_host_admin_username}
           StrictHostKeyChecking no
           UserKnownHostsFile /dev/null
           ProxyCommand ${module.jump.ssh_command} -- -W %h:%p
    
    4. In VS Code: Ctrl+Shift+P > "Remote-SSH: Connect to Host..." > azure-jump
    
    See terraform/modules/jump/README.md for detailed setup instructions.
  EOT
  description = "Quick setup guide for accessing the jump host via VS Code Remote SSH."
}
