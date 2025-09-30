resource "azurerm_cosmosdb_account" "main" {
  name                = local.cosmos_account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  automatic_failover_enabled    = false
  free_tier_enabled             = false
  analytical_storage_enabled    = true
  public_network_access_enabled = false

  capabilities {
    name = "EnableServerless"
  }

  capabilities {
    name = "EnableNoSQLVectorSearch"
  }

  consistency_policy {
    consistency_level       = "Session"
    max_staleness_prefix    = 100
    max_interval_in_seconds = 5
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  backup {
    type = "Continuous"
    tier = "Continuous30Days"
  }

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "appdb"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
}

resource "azurerm_cosmosdb_sql_container" "products" {
  name                  = "products"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths   = ["/category"]
  partition_key_version = 2

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

resource "azapi_update_resource" "products_vector_index" {
  type        = "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15-preview"
  resource_id = azurerm_cosmosdb_sql_container.products.id

  body = {
    properties = {
      indexingPolicy = {
        indexingMode = "consistent"
        includedPaths = [
          {
            path = "/*"
          }
        ]
        vectorIndexes = [
          {
            path           = "/embedding"
            type           = "quantizedFloatVectorIndex"
            dataType       = "float32"
            dimensions     = 1536
            distanceMetric = "cosine"
            algorithmConfig = {
              kind = "hnsw"
              parameters = {
                m              = 16
                efConstruction = 400
              }
            }
          }
        ]
      }
    }
  }

  depends_on = [azurerm_cosmosdb_sql_container.products]
}

resource "azurerm_cosmosdb_sql_container" "pricing" {
  name                  = "pricing"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths   = ["/product_id"]
  partition_key_version = 2

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

resource "azurerm_cosmosdb_sql_container" "stock" {
  name                  = "stock"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths   = ["/product_id"]
  partition_key_version = 2
}

resource "azurerm_cosmosdb_sql_container" "user_profiles" {
  name                  = "user_profiles"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths   = ["/user_id"]
  partition_key_version = 2
}

resource "azurerm_private_endpoint" "cosmos" {
  name                = "pep-cosmos-${var.base_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_ids["snet-pes"]
  tags                = var.tags

  private_service_connection {
    name                           = "psc-cosmos-${var.base_name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_cosmosdb_account.main.id
    subresource_names              = ["Sql"]
  }

  private_dns_zone_group {
    name                 = "pdz-cosmos"
    private_dns_zone_ids = [var.private_dns_zone_ids["cosmos"]]
  }
}

