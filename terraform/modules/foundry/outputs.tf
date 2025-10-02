output "cognitive_account_id" {
  description = "Resource ID of the Azure AI Foundry account."
  value       = azapi_resource.ai_foundry.id
}

output "cognitive_account_endpoint" {
  description = "Endpoint URI for the Azure AI Foundry account."
  value       = tostring(azapi_resource.ai_foundry.output["properties"]["endpoint"])
}

output "embeddings_endpoint" {
  description = "Endpoint URI for embeddings model deployment (for use with Azure OpenAI SDK)."
  value       = "${tostring(azapi_resource.ai_foundry.output["properties"]["endpoint"])}models"
}

output "model_deployment_ids" {
  description = "Map of Azure AI Foundry deployment resource IDs keyed by deployment name."
  value = {
    for deployment_name, deployment in azapi_resource.deployment :
    deployment_name => deployment.id
  }
}
