resource "azurerm_resource_group" "rg" {
  name     = "${var.resource_group_name}-${var.service_name}-${var.environment}"
  location = var.resource_group_location
}