# Search engines, documentation, and additional dependencies
resource "azurerm_firewall_policy_rule_collection_group" "web_services" {
  name               = "fwpol-rcg-web-services"
  firewall_policy_id = azurerm_firewall_policy.main.id
  priority           = 400

  application_rule_collection {
    name     = "search-engines"
    priority = 400
    action   = "Allow"

    rule {
      name = "search-tavily-google-bing"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.google.com",
        "*.bing.com",
        "*.search.msn.com",
        "api.tavily.com",
        "tavily.com"
      ]
    }
  }

  application_rule_collection {
    name     = "microsoft-docs"
    priority = 410
    action   = "Allow"

    rule {
      name = "microsoft-learn-documentation"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "learn.microsoft.com",
        "docs.microsoft.com",
        "*.docs.microsoft.com",
        "aka.ms",
        "go.microsoft.com"
      ]
    }
  }

  application_rule_collection {
    name     = "container-registries"
    priority = 420
    action   = "Allow"

    rule {
      name = "mcr-base-images"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "mcr.microsoft.com",
        "*.mcr.microsoft.com",
        "*.data.mcr.microsoft.com",
        "*.cdn.mscr.io"
      ]
    }
  }

  application_rule_collection {
    name     = "cdn-static-assets"
    priority = 430
    action   = "Allow"

    rule {
      name = "cdn-azure-office"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.cdn.office.net",
        "*.azureedge.net",
        "*.visualstudio.com",
        "*.azure-dns.com",
        "*.azure-dns.net"
      ]
    }
  }
}
