# Create an Azure Key Vault
resource "azurerm_key_vault" "keyvault" {
  name                        = "${var.service_name}-${var.environment}"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"

  # Access Policies (optional, add your own service principal)
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "get",
      "set",
      "delete",
      "list"
    ]
  }
}

# Generate a random password
resource "random_password" "password" {
  length  = 16
  special = true
}

# Store the password in Azure Key Vault as a secret
resource "azurerm_key_vault_secret" "keycloak_password" {
  name         = "keycloak-admin-password"
  value        = random_password.password.result
  key_vault_id = azurerm_key_vault.keyvault.id
}
