
resource "azurerm_container_registry" "acridentity" {
  name                = "${var.service_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  admin_enabled       = true
  sku                 = "Basic"
}

resource "azurerm_role_assignment" "acr" {
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acridentity.id
  principal_id         = azurerm_linux_web_app.keycloak.identity[0].principal_id
}