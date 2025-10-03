locals {
  cosmos_account_name = substr("cosmos${var.base_name_nodash}", 0, 44)
}
