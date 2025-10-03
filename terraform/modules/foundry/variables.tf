variable "resource_group_name" {
  type        = string
  description = "Resource group that hosts the Azure AI Foundry account."
}

variable "resource_group_id" {
  type        = string
  description = "Resource group ID used as the parent for Azure AI Foundry resources."
}

variable "location" {
  type        = string
  description = "Azure region for the Azure AI Foundry deployment."
}

variable "base_name" {
  type        = string
  description = "Normalized name suffix shared across resources."
}

variable "tags" {
  type        = map(string)
  description = "Tags inherited by Azure AI Foundry resources."
}

variable "agent_subnet_id" {
  type        = string
  description = "Subnet ID delegated to Microsoft.App/environments for agent network injection."
}

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Subnet ID hosting private endpoints for Foundry supporting services."
}

variable "private_dns_zone_ids" {
  type        = map(string)
  description = "Map of private DNS zone IDs used for Foundry supporting services."
}

variable "jump_host_identity_principal_id" {
  type        = string
  description = "Principal ID of the jump host system-assigned managed identity for Azure AI User role assignment."
}

variable "mcp_identity_principal_id" {
  type        = string
  description = "Principal ID of the MCP server user-assigned managed identity used to grant Cognitive Services OpenAI User role for embeddings access."
}

