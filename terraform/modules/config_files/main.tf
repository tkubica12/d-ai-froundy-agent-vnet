# Config Files Module
#
# This module generates environment configuration files (.env) for various components
# of the solution. It uses Terraform's templatefile function to inject dynamic values
# (endpoints, resource names, etc.) from the deployed infrastructure while keeping
# static configuration easy to modify in the template files.

# Deploy build configuration
resource "local_file" "deploy_env" {
  filename = "${var.repo_root}/deploy/.env"
  content = templatefile("${path.module}/templates/deploy.env.tftpl", {
    acr_name            = var.acr_name
    resource_group_name = var.resource_group_name
    base_name           = var.base_name
  })
  file_permission = "0644"
}

# MCP Server configuration
resource "local_file" "mcp_env" {
  filename = "${var.repo_root}/src/tools/products_mcp/.env"
  content = templatefile("${path.module}/templates/products_mcp.env.tftpl", {
    cosmos_endpoint       = var.cosmos_endpoint
    cosmos_database_name  = var.cosmos_database_name
    embeddings_endpoint   = var.embeddings_endpoint
    embeddings_deployment = var.embeddings_deployment
    log_level             = var.log_level
  })
  file_permission = "0644"
}

# Facilitator agent configuration
resource "local_file" "facilitator_env" {
  filename = "${var.repo_root}/src/agents/facilitator/.env"
  content = templatefile("${path.module}/templates/agent.env.tftpl", {
    project_endpoint      = var.foundry_project_endpoint
    model_deployment_name = var.model_deployment_name
  })
  file_permission = "0644"
}

# Product Finder agent configuration
resource "local_file" "product_finder_env" {
  filename = "${var.repo_root}/src/agents/product_finder/.env"
  content = templatefile("${path.module}/templates/agent.env.tftpl", {
    project_endpoint      = var.foundry_project_endpoint
    model_deployment_name = var.model_deployment_name
  })
  file_permission = "0644"
}

# Bastion tunnel helper script
resource "local_file" "bastion_tunnel_script" {
  filename = "${var.repo_root}/scripts/connect_bastion_tunnel.ps1"
  content = templatefile("${path.module}/templates/connect_bastion_tunnel.ps1.tftpl", {
    bastion_name        = var.bastion_name
    resource_group_name = var.resource_group_name
    jump_host_ip        = var.jump_host_private_ip
  })
  file_permission = "0755"
}
