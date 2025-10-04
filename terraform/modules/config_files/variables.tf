variable "repo_root" {
  type        = string
  description = <<-EOT
    Absolute path to the repository root directory where configuration files will be generated.
    This should point to the root of the Git repository (parent of src/, deploy/, scripts/, etc.).
    
    Example: "C:/git/d-ai-froundy-agent-vnet" or "/home/user/repos/d-ai-froundy-agent-vnet"
  EOT
}

variable "acr_name" {
  type        = string
  description = "Name of the Azure Container Registry for build/push operations."
}

variable "base_name" {
  type        = string
  description = "Base name used for resource naming (extracted from ACR or resource group naming convention)."
}

variable "cosmos_endpoint" {
  type        = string
  description = "Azure Cosmos DB account endpoint URI (e.g., https://cosmosname.documents.azure.com:443/)."
}

variable "cosmos_database_name" {
  type        = string
  description = "Name of the Cosmos DB database used by the application."
}

variable "embeddings_endpoint" {
  type        = string
  description = <<-EOT
    Endpoint URI for the embeddings model deployment. This is typically the Azure AI Foundry
    cognitive account endpoint (e.g., https://projectname.cognitiveservices.azure.com).
  EOT
}

variable "embeddings_deployment" {
  type        = string
  description = <<-EOT
    Name of the embeddings model deployment from the deployed AI Foundry resources.
    This value is passed from the foundry module's deployment configuration.
  EOT
}

variable "foundry_project_endpoint" {
  type        = string
  description = <<-EOT
    Azure AI Foundry project endpoint URI from deployed infrastructure.
    This value is passed from the foundry module outputs.
    Format: https://<project-name>.services.ai.azure.com/api/projects/<project-id>
  EOT
}

variable "model_deployment_name" {
  type        = string
  description = <<-EOT
    Name of the LLM deployment from deployed AI Foundry resources.
    This value is passed from the foundry module's deployment configuration.
  EOT
}

variable "mcp_server_url" {
  type        = string
  description = <<-EOT
    URL of the MCP (Model Context Protocol) server for product catalog tools.
    This is the Container Apps endpoint where the products MCP server is deployed.
    Format: https://<app-name>.<region>.azurecontainerapps.io/mcp
  EOT
}

variable "resource_group_name" {
  type        = string
  description = "Name of the Azure resource group containing the infrastructure."
}

variable "bastion_name" {
  type        = string
  description = "Name of the Azure Bastion host for jump host connectivity."
}

variable "jump_host_private_ip" {
  type        = string
  description = "Private IP address of the jump host VM for SSH tunneling."
}

variable "log_level" {
  type        = string
  description = "Python logging level for application components (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
  }
}
