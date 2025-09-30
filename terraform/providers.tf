terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }

    azapi = {
      source  = "azure/azapi"
      version = ">= 2.0.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }

    time = {
      source  = "hashicorp/time"
      version = ">= 0.11.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "azapi" {}

provider "time" {}
