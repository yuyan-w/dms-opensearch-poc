# envs/test/variables.tf
variable "aws_region" {
  type    = string
  default = "ap-northeast-1"
}

variable "project_settings" {
  type = object({
    project = string
    env     = string
  })

  default = {
    project = "dms"
    env     = "test"
  }
}

variable "home_ip" {
  type = string
}