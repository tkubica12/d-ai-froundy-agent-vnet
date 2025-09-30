variable "resource_group_name" {
  type        = string
  description = "Resource group where the jump host and bastion will be created."
}

variable "location" {
  type        = string
  description = "Azure region for jump resources."
}

variable "base_name" {
  type        = string
  description = "Normalized suffix applied to resource names."
}

variable "tags" {
  type        = map(string)
  description = "Tags added to jump resources."
}

variable "bastion_subnet_id" {
  type        = string
  description = "Subnet ID dedicated to Azure Bastion."
}

variable "jump_subnet_id" {
  type        = string
  description = "Subnet ID for the jump virtual machine."
}

variable "admin_username" {
  type        = string
  description = "Administrator username for the jump host."
}

variable "admin_password" {
  type        = string
  description = "Administrator password for the jump host."
  sensitive   = true
}
