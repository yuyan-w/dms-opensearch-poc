# modules/opensearch/variables.tf
variable "project_settings" {
  type = object({
    project = string
    env     = string
  })
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}