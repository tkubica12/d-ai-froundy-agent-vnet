variable "resource_group_name" {
  type        = string
  description = "Resource group that will contain networking assets."
}

variable "location" {
  type        = string
  description = "Azure region for networking resources."
}

variable "base_name" {
  type        = string
  description = "Normalized base name appended to networking resource identifiers."
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to networking resources."
}

variable "address_space" {
  type        = list(string)
  description = "Address space allocated to the virtual network."
  default     = ["172.21.0.0/16"]
}

variable "private_dns_zone_names" {
  type        = map(string)
  description = "Private DNS zones to provision and link to the virtual network."
  default = {
    cosmos            = "privatelink.documents.azure.com"
    acr               = "privatelink.azurecr.io"
    storage           = "privatelink.blob.core.windows.net"
    search            = "privatelink.search.windows.net"
    cognitiveservices = "privatelink.cognitiveservices.azure.com"
    services_ai       = "privatelink.services.ai.azure.com"
    openai            = "privatelink.openai.azure.com"
  }
}

variable "firewall_allowed_fqdns" {
  type        = list(string)
  description = "List of FQDNs permitted for outbound access through the firewall."
  default = [
    "login.microsoftonline.com",
    "management.azure.com",
    "packages.microsoft.com",
    "mcr.microsoft.com"
  ]
}
