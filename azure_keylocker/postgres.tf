resource "azurerm_postgresql_server" "keycloakdbserver" {
  resource_group_name              = azurerm_resource_group.rg.name
  location                         = azurerm_resource_group.rg.location
  name                             = "${var.service_name}-${var.environment}-postgres"
  sku_name                         = var.keycloak_db_configuration.sku_name
  version                          = var.keycloak_db_configuration.version
  ssl_enforcement_enabled          = true
  ssl_minimal_tls_version_enforced = "TLS1_2"
  administrator_login = var.keycloak_db_configuration.db_user
  administrator_login_password = random_password.password.result
}

resource "azurerm_postgresql_database" "keycloakdb" {
  name                = var.keycloak_db_configuration.postgresql_database_name
  resource_group_name = azurerm_resource_group.rg.name
  charset             = "UTF8"
  collation           = var.keycloak_db_configuration.collation
  server_name         = azurerm_postgresql_server.keycloakdbserver.name
}

resource "azurerm_postgresql_firewall_rule" "allowaccesstokeycloakdb" {
  name                = "Access-keycloakdb-${var.environment}"
  resource_group_name = azurerm_resource_group.rg.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
  server_name         = azurerm_postgresql_server.keycloakdbserver.name
}