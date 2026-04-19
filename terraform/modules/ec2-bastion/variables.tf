# modules/ec2-bastion/variables.tf
variable "project_settings" {
  type = object({
    project = string
    env     = string
  })
}

variable "subnet_id" {
  type = string
}

variable "vpc_security_group_ids" {
  type = list(string)
}

variable "key_name" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "m8a.medium"
}

variable "ami_id" {
  type    = string
  default = null
}

variable "private_ip" {
  type    = string
  default = null
}