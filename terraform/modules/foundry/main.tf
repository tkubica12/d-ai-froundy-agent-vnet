locals {
  base_compact         = lower(replace(var.base_name, "-", ""))
  custom_subdomain     = lower(substr(local.base_compact, 0, 23))
  storage_account_name = substr("st${local.base_compact}", 0, 24)
  cosmos_account_name  = substr("cosmos${local.base_compact}agent", 0, 44)
  search_service_name  = substr("search${local.base_compact}", 0, 60)
  project_name         = substr("project-${local.base_compact}", 0, 63)
  capability_host_name = "caphost-standard"

  deployments = {
    "gpt-5" = {
      model_name    = "gpt-5"
      model_version = "2025-08-07"
    }
    "gpt-5-mini" = {
      model_name    = "gpt-5-mini"
      model_version = "2025-08-07"
    }
    "gpt-4.1" = {
      model_name    = "gpt-4.1"
      model_version = "2025-04-14"
    }
  }
}

resource "azurerm_storage_account" "agent" {
  name                            = local.storage_account_name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_kind                    = "StorageV2"
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  public_network_access_enabled   = true
  shared_access_key_enabled       = true

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "storage" {
  name                = "pep-${azurerm_storage_account.agent.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${azurerm_storage_account.agent.name}"
    private_connection_resource_id = azurerm_storage_account.agent.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdz-storage"
    private_dns_zone_ids = [var.private_dns_zone_ids["storage"]]
  }
}

resource "azurerm_cosmosdb_account" "agent" {
  name                = local.cosmos_account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  automatic_failover_enabled       = false
  free_tier_enabled                = false
  analytical_storage_enabled       = false
  public_network_access_enabled    = false
  local_authentication_disabled    = true
  multiple_write_locations_enabled = false

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
    zone_redundant    = false
  }

  backup {
    type = "Continuous"
    tier = "Continuous30Days"
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "cosmos" {
  name                = "pep-${azurerm_cosmosdb_account.agent.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${azurerm_cosmosdb_account.agent.name}"
    private_connection_resource_id = azurerm_cosmosdb_account.agent.id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdz-cosmos"
    private_dns_zone_ids = [var.private_dns_zone_ids["cosmos"]]
  }
}

resource "azapi_resource" "search" {
  type                      = "Microsoft.Search/searchServices@2025-05-01"
  name                      = local.search_service_name
  parent_id                 = var.resource_group_id
  location                  = var.location
  schema_validation_enabled = true

  body = {
    sku = {
      name = "standard"
    }

    identity = {
      type = "SystemAssigned"
    }

    properties = {
      replicaCount   = 1
      partitionCount = 1
      hostingMode    = "default"
      semanticSearch = "disabled"

      disableLocalAuth = false
      authOptions = {
        aadOrApiKey = {
          aadAuthFailureMode = "http401WithBearerChallenge"
        }
      }

      publicNetworkAccess = "Disabled"
      networkRuleSet = {
        bypass = "None"
      }
    }
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "search" {
  name                = "pep-${local.search_service_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${local.search_service_name}"
    private_connection_resource_id = azapi_resource.search.id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name = "pdz-search"
    private_dns_zone_ids = [
      var.private_dns_zone_ids["search"]
    ]
  }
}

resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "cog-${var.base_name}"
  parent_id                 = var.resource_group_id
  location                  = var.location
  schema_validation_enabled = false
  tags                      = var.tags

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      customSubDomainName    = local.custom_subdomain
      allowProjectManagement = true
      disableLocalAuth       = false
      publicNetworkAccess    = "Disabled"
      networkAcls = {
        defaultAction = "Allow"
      }
      networkInjections = [
        {
          scenario                   = "agent"
          subnetArmId                = var.agent_subnet_id
          useMicrosoftManagedNetwork = false
        }
      ]
    }
  }

  response_export_values = ["properties.endpoint"]
}

resource "azurerm_private_endpoint" "foundry" {
  name                = "pep-${azapi_resource.ai_foundry.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${azapi_resource.ai_foundry.name}"
    private_connection_resource_id = azapi_resource.ai_foundry.id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name = "pdz-foundry"
    private_dns_zone_ids = [
      var.private_dns_zone_ids["cognitiveservices"],
      var.private_dns_zone_ids["services_ai"],
      var.private_dns_zone_ids["openai"]
    ]
  }
}

resource "azapi_resource" "deployment" {
  for_each                  = local.deployments
  type                      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name                      = each.value.model_name
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 50
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = each.value.model_name
        version = each.value.model_version
      }
    }
  }
}

resource "azapi_resource" "ai_foundry_project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = local.project_name
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = var.location
  schema_validation_enabled = false

  depends_on = [
    azurerm_private_endpoint.storage,
    azurerm_private_endpoint.cosmos,
    azurerm_private_endpoint.search,
    azurerm_private_endpoint.foundry
  ]

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "project"
      description = "Standard agent project with VNet injection"
    }
  }

  response_export_values = [
    "identity.principalId",
    "properties.internalId"
  ]
}

resource "time_sleep" "wait_project_identity" {
  depends_on      = [azapi_resource.ai_foundry_project]
  create_duration = "10s"
}

locals {
  project_internal_id = tostring(azapi_resource.ai_foundry_project.output["properties"]["internalId"])
  project_id_guid = join("-", [
    substr(local.project_internal_id, 0, 8),
    substr(local.project_internal_id, 8, 4),
    substr(local.project_internal_id, 12, 4),
    substr(local.project_internal_id, 16, 4),
    substr(local.project_internal_id, 20, 12)
  ])
}

resource "azapi_resource" "conn_cosmos" {
  type                      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name                      = azurerm_cosmosdb_account.agent.name
  parent_id                 = azapi_resource.ai_foundry_project.id
  schema_validation_enabled = false

  depends_on = [time_sleep.wait_project_identity]

  body = {
    name = azurerm_cosmosdb_account.agent.name
    properties = {
      category = "CosmosDb"
      target   = azurerm_cosmosdb_account.agent.endpoint
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_cosmosdb_account.agent.id
        location   = var.location
      }
    }
  }
}

resource "azapi_resource" "conn_storage" {
  type                      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name                      = azurerm_storage_account.agent.name
  parent_id                 = azapi_resource.ai_foundry_project.id
  schema_validation_enabled = false

  depends_on = [time_sleep.wait_project_identity]

  body = {
    name = azurerm_storage_account.agent.name
    properties = {
      category = "AzureStorageAccount"
      target   = azurerm_storage_account.agent.primary_blob_endpoint
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_storage_account.agent.id
        location   = var.location
      }
    }
  }
}

resource "azapi_resource" "conn_search" {
  type                      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name                      = local.search_service_name
  parent_id                 = azapi_resource.ai_foundry_project.id
  schema_validation_enabled = false

  depends_on = [time_sleep.wait_project_identity]

  body = {
    name = local.search_service_name
    properties = {
      category = "CognitiveSearch"
      target   = "https://${local.search_service_name}.search.windows.net"
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ApiVersion = "2025-05-01-preview"
        ResourceId = azapi_resource.search.id
        location   = var.location
      }
    }
  }
}

resource "azurerm_role_assignment" "cosmos_operator" {
  scope                = azurerm_cosmosdb_account.agent.id
  role_definition_name = "Cosmos DB Operator"
  principal_id         = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_project_identity]

  name = uuidv5("dns", "${local.project_name}-${azurerm_cosmosdb_account.agent.name}-cosmos-operator")
}

resource "azurerm_role_assignment" "storage_blob_contributor" {
  scope                = azurerm_storage_account.agent.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_project_identity]

  name = uuidv5("dns", "${local.project_name}-${azurerm_storage_account.agent.name}-blob-contributor")
}

resource "azurerm_role_assignment" "search_index_data_contributor" {
  scope                = azapi_resource.search.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_project_identity]

  name = uuidv5("dns", "${local.project_name}-${local.search_service_name}-search-index")
}

resource "azurerm_role_assignment" "search_service_contributor" {
  scope                = azapi_resource.search.id
  role_definition_name = "Search Service Contributor"
  principal_id         = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_project_identity]

  name = uuidv5("dns", "${local.project_name}-${local.search_service_name}-search-service")
}

resource "time_sleep" "wait_rbac" {
  depends_on = [
    azurerm_role_assignment.cosmos_operator,
    azurerm_role_assignment.storage_blob_contributor,
    azurerm_role_assignment.search_index_data_contributor,
    azurerm_role_assignment.search_service_contributor
  ]
  create_duration = "60s"
}

resource "azapi_resource" "capability_host" {
  type                      = "Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-04-01-preview"
  name                      = local.capability_host_name
  parent_id                 = azapi_resource.ai_foundry_project.id
  schema_validation_enabled = false

  depends_on = [
    azapi_resource.conn_cosmos,
    azapi_resource.conn_storage,
    azapi_resource.conn_search,
    time_sleep.wait_rbac
  ]

  body = {
    properties = {
      capabilityHostKind = "Agents"
      vectorStoreConnections = [
        azapi_resource.search.name
      ]
      storageConnections = [
        azurerm_storage_account.agent.name
      ]
      threadStorageConnections = [
        azurerm_cosmosdb_account.agent.name
      ]
    }
  }
}

resource "time_sleep" "wait_capability_host" {
  depends_on      = [azapi_resource.capability_host]
  create_duration = "30s"
}

resource "azurerm_cosmosdb_sql_role_assignment" "thread_message_store" {
  name                = uuidv5("dns", "${local.project_name}-${local.project_id_guid}-thread-message")
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.agent.name
  scope               = "${azurerm_cosmosdb_account.agent.id}/dbs/enterprise_memory/colls/${local.project_id_guid}-thread-message-store"
  role_definition_id  = "${azurerm_cosmosdb_account.agent.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_capability_host]
}

resource "azurerm_cosmosdb_sql_role_assignment" "system_thread_store" {
  name                = uuidv5("dns", "${local.project_name}-${local.project_id_guid}-system-thread")
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.agent.name
  scope               = "${azurerm_cosmosdb_account.agent.id}/dbs/enterprise_memory/colls/${local.project_id_guid}-system-thread-message-store"
  role_definition_id  = "${azurerm_cosmosdb_account.agent.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [azurerm_cosmosdb_sql_role_assignment.thread_message_store]
}

resource "azurerm_cosmosdb_sql_role_assignment" "agent_entity_store" {
  name                = uuidv5("dns", "${local.project_name}-${local.project_id_guid}-agent-entity")
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.agent.name
  scope               = "${azurerm_cosmosdb_account.agent.id}/dbs/enterprise_memory/colls/${local.project_id_guid}-agent-entity-store"
  role_definition_id  = "${azurerm_cosmosdb_account.agent.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [azurerm_cosmosdb_sql_role_assignment.system_thread_store]
}

resource "azurerm_role_assignment" "storage_blob_owner_restricted" {
  scope                = azurerm_storage_account.agent.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azapi_resource.ai_foundry_project.output["identity"]["principalId"]

  depends_on = [time_sleep.wait_capability_host]

  condition_version = "2.0"
  condition         = <<-EOT
    (
      (
        !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/read'})
        AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action'})
        AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write'})
      )
      OR
      (@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringStartsWithIgnoreCase '${local.project_id_guid}'
        AND @Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringLikeIgnoreCase '*-azureml-agent')
    )
  EOT

  name = uuidv5("dns", "${local.project_name}-${azurerm_storage_account.agent.name}-blob-owner")
}
