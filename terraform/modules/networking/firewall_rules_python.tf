# Python package managers: pip, PyPI, uv (Astral)
resource "azurerm_firewall_policy_rule_collection_group" "python_packages" {
  name               = "fwpol-rcg-python-packages"
  firewall_policy_id = azurerm_firewall_policy.main.id
  priority           = 300

  application_rule_collection {
    name     = "python-pip-pypi"
    priority = 300
    action   = "Allow"

    rule {
      name = "python-package-index"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "pypi.org",
        "*.pypi.org",
        "files.pythonhosted.org",
        "pypi.python.org",
        "*.python.org"
      ]
    }
  }

  application_rule_collection {
    name     = "python-uv-astral"
    priority = 310
    action   = "Allow"

    rule {
      name = "uv-package-manager"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "astral.sh",
        "*.astral.sh",
        "pypi.org",
        "files.pythonhosted.org"
      ]
    }
  }
}
