variable "resource_group_name" {
  type        = string
  description = "Resource group hosting application platform assets."
}

variable "location" {
  type        = string
  description = "Azure region for application resources."
}

variable "base_name" {
  type        = string
  description = "Normalized base name suffix used for naming resources."
}

variable "base_name_nodash" {
  type        = string
  description = "Base name variant without dashes for services with stricter naming requirements."
}

variable "tags" {
  type        = map(string)
  description = "Tags propagated to application resources."
}

variable "subnet_ids" {
  type        = map(string)
  description = "Map of subnet identifiers provided by the networking module."
}

variable "private_dns_zone_ids" {
  type        = map(string)
  description = "Private DNS zone identifiers used for private endpoints."
}

variable "backend_image" {
  type        = string
  description = "Container image for the FastAPI backend."
  default     = null
}

variable "frontend_image" {
  type        = string
  description = "Container image for the React assistant UI."
  default     = null
}

variable "mcp_image" {
  type        = string
  description = <<-DESC
    Container image for the Products MCP server.
    If not provided, defaults to products-mcp:latest in the provisioned ACR.
  DESC
  default     = null
}

variable "jump_vm_principal_id" {
  type        = string
  description = <<-DESC
    Principal ID (object ID) of the jump VM's system-assigned managed identity.
    Used to grant Cosmos DB RBAC access for testing the MCP server from the jump host.
    Optional - if not provided (empty string), jump VM will not have data plane access.
  DESC
  default     = ""
}

variable "embeddings_endpoint" {
  type        = string
  description = <<-DESC
    Azure OpenAI endpoint for embeddings model.
    Should be the base endpoint from Azure AI Foundry (e.g., https://xyz.cognitiveservices.azure.com).
  DESC
}

