variable "project_settings" {
  type = object({
    project = string
    env     = string
  })
}

variable "subnet_ids" {
  type = list(string)
}

variable "dms_vpc_security_group_ids" {
  type = list(string)
}

variable "aurora_server_name" {
  type = string
}

variable "aurora_username" {
  type = string
}

variable "aurora_password" {
  type      = string
  sensitive = true
}

variable "opensearch_endpoint" {
  type = string
}

variable "opensearch_domain_arn" {
  type = string
}