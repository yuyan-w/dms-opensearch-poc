variable "project_settings" {
  description = "Project settings including project name and environment"
  type = object({
    project = string
    env     = string
  })
}
