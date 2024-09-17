resource "azurerm_service_plan" "svc_plan" {
  name                = "${var.resource_group_name}-${var.service_name}-${var.environment}-svc-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "P1v2"
}

resource "azurerm_linux_web_app" "keycloak" {
  name                = "${var.resource_group_name}-${var.service_name}-${var.environment}-app"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_service_plan.svc_plan.location
  service_plan_id     = azurerm_service_plan.svc_plan.id

   https_only              = true

  site_config {
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name     = "${azurerm_container_registry.acridentity.login_server}/keycloack:latest"
      docker_registry_url  ="${azurerm_container_registry.acridentity.login_server}"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL" = "https://${azurerm_container_registry.acridentity.name}.azurecr.io"
    "KC_DB": "postgres"
    "KC_DB_URL_HOST": "${azurerm_postgresql_server.keycloakdbserver.fqdn}"
    "KC_DB_URL_PORT": 5432
    "KC_DB_URL_DATABASE": "${azurerm_postgresql_database.keycloakdb.name}"
    "KC_DB_USERNAME": "${var.keycloak_db_configuration.db_user}@${azurerm_postgresql_server.keycloakdbserver.name}"
    "KC_DB_PASSWORD": "${random_password.password.result}"
    "KC_PROXY": "edge"
    "WEBSITES_PORT": 8080
    "KEYCLOAK_ADMIN" = "${var.keycloak_db_configuration.db_user}"
    "KEYCLOAK_ADMIN_PASSWORD" = "${random_password.password.result}"
  }
}