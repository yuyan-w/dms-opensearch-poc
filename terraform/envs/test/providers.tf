# envs/test/providers.tf
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_settings.project
      Environment = var.project_settings.env
      ManagedBy   = "Terraform"
    }
  }
}