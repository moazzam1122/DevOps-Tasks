variable "resource_group_name" {}
variable "resource_group_location" {}

variable "service_name" {
    type = string
    description = "Name of the service that you are deploying"
}


variable "environment" {
    type = string
    description = "Name of the Env on which you are deploying"
}

variable "keycloak_db_configuration" {
  description = "Configuration for the Keycloak PostgreSQL database"
  type = object({
    db_user                 = string
    sku_name                = string
    version                 = string
    postgresql_database_name = string
    collation               = string
  })
}