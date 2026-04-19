variable "project_settings" {
  type = object({
    project = string
    env     = string
  })
}

variable "subnet_ids" {
  type = list(string)
}

variable "vpc_security_group_ids" {
  type = list(string)
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "master_username" {
  type = string
}

variable "master_password" {
  type      = string
  sensitive = true
}

variable "instance_class" {
  type    = string
  default = "db.r8g.large"
}

variable "engine_version" {
  type    = string
  default = "8.0.mysql_aurora.3.08.2"
}

variable "backup_retention_period" {
  type    = number
  default = 1
}

variable "preferred_backup_window" {
  type    = string
  default = "18:00-19:00"
}

variable "preferred_maintenance_window" {
  type    = string
  default = "sun:19:00-sun:20:00"
}

variable "vpc_id" {
  type = string
}