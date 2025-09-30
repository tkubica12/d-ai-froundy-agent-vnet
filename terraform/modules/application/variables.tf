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
