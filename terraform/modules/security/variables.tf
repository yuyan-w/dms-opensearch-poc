variable "project_settings" {
  description = "Project settings including project name and environment"
  type = object({
    project = string
    env     = string
  })
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "home_ip" {
  description = "Home IP address for SSH access (CIDR format)"
  type        = string
  # 例: "203.0.113.0/32"
}
