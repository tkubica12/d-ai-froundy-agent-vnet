# Developer tools: Azure CLI, Terraform, VS Code, Git, GitHub CLI
resource "azurerm_firewall_policy_rule_collection_group" "developer_tools" {
  name               = "fwpol-rcg-developer-tools"
  firewall_policy_id = azurerm_firewall_policy.main.id
  priority           = 200

  application_rule_collection {
    name     = "azure-services"
    priority = 200
    action   = "Allow"

    rule {
      name = "azure-management-auth"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.azure.com",
        "*.azure.net",
        "*.azureedge.net",
        "*.azure-api.net",
        "*.azurewebsites.net",
        "*.azurecr.io",
        "*.blob.core.windows.net",
        "*.servicebus.windows.net",
        "management.azure.com",
        "login.microsoftonline.com",
        "login.windows.net",
        "graph.microsoft.com",
        "*.applicationinsights.azure.com",
        "*.monitor.azure.com",
        "*.prod.warm.ingest.monitor.core.windows.net",
        "gcs.prod.monitoring.core.windows.net"
      ]
    }

    rule {
      name = "azure-cli-installation"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "aka.ms",
        "packages.microsoft.com",
        "azurecliprod.blob.core.windows.net",
        "*.azcliext.blob.core.windows.net"
      ]
    }
  }

  application_rule_collection {
    name     = "github-git"
    priority = 210
    action   = "Allow"

    rule {
      name = "github-repositories-cli"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "github.com",
        "*.github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com",
        "github-releases.githubusercontent.com",
        "codeload.github.com",
        "cli.github.com"
      ]
    }

    rule {
      name = "github-s3-assets"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "github-production-release-asset-2e65be.s3.amazonaws.com"
      ]
    }
  }

  application_rule_collection {
    name     = "hashicorp-terraform"
    priority = 220
    action   = "Allow"

    rule {
      name = "terraform-releases-registry"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "releases.hashicorp.com",
        "*.hashicorp.com",
        "registry.terraform.io",
        "checkpoint-api.hashicorp.com"
      ]
    }
  }

  application_rule_collection {
    name     = "python-uv-astral"
    priority = 225
    action   = "Allow"

    rule {
      name = "uv-installer"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "astral.sh",
        "*.astral.sh"
      ]
    }
  }

  application_rule_collection {
    name     = "vscode"
    priority = 230
    action   = "Allow"

    rule {
      name = "vscode-updates-extensions"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.vscode-cdn.net",
        "*.vsassets.io",
        "*.vscode.dev",
        "vscode.download.prss.microsoft.com",
        "update.code.visualstudio.com",
        "marketplace.visualstudio.com",
        "*.gallery.vsassets.io",
        "*.gallerycdn.vsassets.io"
      ]
    }
  }
}
