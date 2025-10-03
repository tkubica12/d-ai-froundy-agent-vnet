variable "subscription_id" {
  description = "Subscription that will host the private agent environment."
  type        = string
  default     = "673af34d-6b28-41dc-bc7b-f507418045e6"
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "swedencentral"
}

variable "prefix" {
  description = "Short name used as a prefix for all resource names."
  type        = string
  default     = "daf"
}

variable "tags" {
  description = "Common tags applied to every resource."
  type        = map(string)
  default = {
    environment = "dev"
  }
}

variable "backend_image" {
  description = "Optional override for the backend container image reference."
  type        = string
  default     = null
}

variable "frontend_image" {
  description = "Optional override for the frontend container image reference."
  type        = string
  default     = null
}

variable "jump_host_admin_username" {
  description = "Admin username for the jump host virtual machine."
  type        = string
  default     = "azureuser"
}

variable "jump_host_admin_password" {
  description = "Password supplied to the Windows jump host VM."
  type        = string
  sensitive   = true
}

variable "jump_host_admin_ssh_key" {
  description = <<-DESC
    SSH public key for the jump host administrator account.
    Enables SSH key authentication alongside password authentication.
    Format: "ssh-rsa AAAAB3NzaC1yc2E... user@hostname"
    Leave empty to use password-only authentication.
  DESC
  type        = string
  sensitive   = true
  default     = ""
}

# Configuration Files Module Variables

variable "repo_root" {
  description = <<-DESC
    Absolute path to the repository root directory for generating configuration files.
    This should point to the root of the Git repository (parent of src/, deploy/, scripts/).
    
    Example Windows: "C:/git/d-ai-froundy-agent-vnet"
    Example Linux: "/home/user/repos/d-ai-froundy-agent-vnet"
  DESC
  type        = string
}

variable "log_level" {
  description = "Python logging level for application components (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
  }
}
