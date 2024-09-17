output "app_service_default_hostname" {
  description = "The default hostname of the App Service"
  value       = azurerm_linux_web_app.keycloak.default_hostname
}

output "app_service_url" {
  description = "The fully qualified URL of the App Service"
  value       = "https://${azurerm_linux_web_app.keycloak.default_hostname}"
}

output "app_service_id" {
  description = "The resource ID of the App Service"
  value       = azurerm_linux_web_app.keycloak.id
}