locals {
  cosmos_account_name  = substr("cosmos${var.base_name_nodash}", 0, 44)
  backend_internal_url = "http://aca-backend-${var.base_name}.internal"
}
