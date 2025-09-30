output "virtual_network_id" {
  value       = azurerm_virtual_network.main.id
  description = "Identifier of the deployed virtual network."
}

output "subnet_ids" {
  value       = { for key, subnet in azurerm_subnet.main : key => subnet.id }
  description = "Map of subnet logical keys to subnet resource identifiers."
}

output "firewall_id" {
  value       = azurerm_firewall.main.id
  description = "Azure Firewall resource identifier."
}

output "firewall_private_ip" {
  value       = azurerm_firewall.main.ip_configuration[0].private_ip_address
  description = "Private IP address of the firewall for routing traffic."
}

output "route_table_id" {
  value       = azurerm_route_table.main.id
  description = "Route table directing outbound flows through the firewall."
}

output "private_dns_zone_ids" {
  value       = { for key, zone in azurerm_private_dns_zone.this : key => zone.id }
  description = "Map of private DNS zone keys to their IDs."
}
