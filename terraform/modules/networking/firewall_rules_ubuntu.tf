# Ubuntu/Linux system updates and package management
resource "azurerm_firewall_policy_rule_collection_group" "ubuntu_essential" {
  name               = "fwpol-rcg-ubuntu-essential"
  firewall_policy_id = azurerm_firewall_policy.main.id
  priority           = 100

  application_rule_collection {
    name     = "ubuntu-updates-repos"
    priority = 100
    action   = "Allow"

    rule {
      name = "ubuntu-apt-repositories"
      protocols {
        type = "Https"
        port = 443
      }
      protocols {
        type = "Http"
        port = 80
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.ubuntu.com",
        "*.archive.ubuntu.com",
        "security.ubuntu.com",
        "archive.ubuntu.com",
        "ports.ubuntu.com",
        "changelogs.ubuntu.com",
        "*.canonical.com",
        "keyserver.ubuntu.com",
        "api.snapcraft.io",
        "*.launchpad.net"
      ]
    }
  }

  application_rule_collection {
    name     = "ca-certificates-ocsp"
    priority = 110
    action   = "Allow"

    rule {
      name = "certificate-validation"
      protocols {
        type = "Https"
        port = 443
      }
      protocols {
        type = "Http"
        port = 80
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "ocsp.digicert.com",
        "*.digicert.com",
        "ocsp.sectigo.com",
        "crl.sectigo.com",
        "*.letsencrypt.org",
        "ocsp.microsoft.com",
        "oneocsp.microsoft.com",
        "crl.microsoft.com"
      ]
    }
  }

  application_rule_collection {
    name     = "ntp-time-sync"
    priority = 120
    action   = "Allow"

    rule {
      name = "ntp-servers"
      protocols {
        type = "Https"
        port = 443
      }
      protocols {
        type = "Http"
        port = 80
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "ntp.ubuntu.com",
        "*.ntp.org",
        "time.cloudflare.com"
      ]
    }
  }
}
