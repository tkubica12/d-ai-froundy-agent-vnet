# Configuration Files Module

This Terraform module generates environment configuration files (`.env`) and helper scripts with values from the deployed Azure infrastructure. It uses Terraform's `templatefile` function to inject dynamic values (endpoints, resource names, etc.) while keeping static configuration easy to modify.

## Purpose

- **Automate configuration**: Eliminates manual copying of resource endpoints and names from Azure Portal or Terraform outputs
- **Single source of truth**: Infrastructure values flow directly from Terraform into application configuration
- **Easy customization**: Template files (`.tftpl`) are simple to modify for static settings
- **Version controlled**: Configuration templates are tracked in Git, generated files are excluded via `.gitignore`

## Generated Files

This module generates the following files in the repository:

| File | Purpose | Template |
|------|---------|----------|
| `deploy/.env` | ACR configuration for build/push scripts | `templates/deploy.env.tftpl` |
| `src/tools/products_mcp/.env` | MCP server Cosmos DB and embeddings config | `templates/products_mcp.env.tftpl` |
| `src/agents/facilitator/.env` | Facilitator agent AI Foundry configuration | `templates/agent.env.tftpl` |
| `src/agents/product_finder/.env` | Product Finder agent AI Foundry configuration | `templates/agent.env.tftpl` |
| `scripts/connect_bastion_tunnel.ps1` | Azure Bastion SSH tunnel helper script | `templates/connect_bastion_tunnel.ps1.tftpl` |

## Usage

Add this module to your root Terraform configuration:

```terraform
module "config_files" {
  source = "./modules/config_files"

  # Repository path
  repo_root = "C:/git/d-ai-froundy-agent-vnet"  # Adjust for your environment

  # Infrastructure values from other modules
  acr_name                   = module.application.container_registry_login_server
  cosmos_endpoint            = "https://${azurerm_cosmosdb_account.main.name}.documents.azure.com:443/"
  cosmos_database_name       = module.application.cosmos_database_name
  embeddings_endpoint        = module.foundry.cognitive_account_endpoint
  foundry_project_endpoint   = "https://your-project.services.ai.azure.com/api/projects/your-id"
  resource_group_name        = azurerm_resource_group.main.name
  bastion_name               = module.jump.bastion_name
  jump_host_private_ip       = module.jump.jump_host_private_ip

  # Optional: Override defaults for MCP tuning parameters
  # vector_top_k              = 30
  # min_similarity_threshold  = 0.6
  # log_level                 = "DEBUG"
}
```

## Customization

### Modifying Templates

Edit template files in `templates/` directory to change structure or add new variables:

```hcl
# Example: templates/products_mcp.env.tftpl
COSMOS_DB_ENDPOINT=${cosmos_endpoint}
COSMOS_DB_NAME=${cosmos_database_name}

# Add your custom static values here
CUSTOM_SETTING=my_value

# Reference more Terraform variables
NEW_VARIABLE=${new_variable}
```

### Adding New Variables

1. Add variable to `variables.tf`:
```terraform
variable "new_variable" {
  type        = string
  description = "Description of the new variable."
  default     = "default_value"
}
```

2. Pass it to template in `main.tf`:
```terraform
content = templatefile("${path.module}/templates/example.env.tftpl", {
  existing_var = var.existing_var
  new_variable = var.new_variable  # Add this line
})
```

3. Use it in template:
```
NEW_VARIABLE=${new_variable}
```

### Tuning MCP Server

The module provides variables for MCP server performance tuning:

- `vector_top_k`: Number of vectors to retrieve (default: 20)
- `min_similarity_threshold`: Minimum similarity score 0.0-1.0 (default: 0.5)
- `similarity_weight`: Weight for similarity in ranking (default: 0.55)
- `popularity_weight`: Weight for popularity in ranking (default: 0.15)
- `price_weight`: Weight for price in ranking (default: 0.15)
- `availability_weight`: Weight for availability in ranking (default: 0.15)

Override in module call:

```terraform
module "config_files" {
  # ... other variables ...
  
  vector_top_k              = 30
  min_similarity_threshold  = 0.6
  similarity_weight         = 0.7
  popularity_weight         = 0.1
  price_weight              = 0.1
  availability_weight       = 0.1
}
```

## Important Notes

### Git Ignore

Generated `.env` files should be excluded from Git (they already are via `.gitignore`):

```gitignore
**/.env
.env
*.env
```

Only the **templates** (`.tftpl`) are version controlled.

### File Permissions

The module sets appropriate permissions:
- `.env` files: `0644` (read/write for owner, read for group/others)
- Scripts: `0755` (executable by owner, read/execute for group/others)

### Terraform Apply

Files are regenerated on every `terraform apply`. If you need to make local changes:

1. Edit the **template** file in `templates/` directory
2. Run `terraform apply` to regenerate all files

### Cross-Platform Paths

The module uses forward slashes (`/`) in path construction, which works on both Windows and Unix:

```terraform
filename = "${var.repo_root}/deploy/.env"  # Works on Windows and Linux
```

Terraform automatically normalizes paths for the target platform.

## Outputs

- `generated_files`: List of all generated file paths
- `deploy_env_path`: Path to deploy/.env
- `mcp_env_path`: Path to MCP server .env

Use outputs for automation:

```terraform
output "config_files" {
  value = module.config_files.generated_files
}
```

## Troubleshooting

### Files Not Generated

Check that `repo_root` points to the correct absolute path:

```bash
# Unix/Linux/macOS
repo_root = "/home/user/repos/d-ai-froundy-agent-vnet"

# Windows
repo_root = "C:/git/d-ai-froundy-agent-vnet"  # Use forward slashes
```

### Permission Denied

Ensure Terraform has write access to the repository directories. On Unix systems, check file ownership:

```bash
ls -la src/tools/products_mcp/.env
```

### Template Syntax Errors

Template syntax uses `${variable}` for Terraform interpolation. For literal `$` in output, escape it:

```
# In template file
LITERAL_DOLLAR=\$not_a_variable
```

## Related Documentation

- [Terraform `templatefile` Function](https://developer.hashicorp.com/terraform/language/functions/templatefile)
- [Terraform `local_file` Resource](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file)
