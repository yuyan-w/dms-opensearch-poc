# envs/test/main.tf
module "network" {
  source = "../../modules/network"

  project_settings = var.project_settings
}

module "security" {
  source = "../../modules/security"

  project_settings = var.project_settings
  vpc_id           = module.network.vpc_id
  home_ip          = var.home_ip
}

module "ec2_bastion" {
  source = "../../modules/ec2-bastion"

  project_settings = var.project_settings
  subnet_id        = module.network.public_subnet_ids[0]
  key_name         = "${var.project_settings.project}-${var.project_settings.env}-ec2-key"

  vpc_security_group_ids = [
    module.security.ec2_security_group_id
  ]
}

module "aurora_mysql" {
  source = "../../modules/aurora"

  project_settings = var.project_settings

  vpc_id     = module.network.vpc_id
  subnet_ids = module.network.aurora_subnet_ids
  vpc_security_group_ids = [
    module.security.aurora_security_group_id
  ]

  db_name         = "dmsapp"
  master_username = "admin"
  master_password = "Password1234!"
  instance_class  = "db.r8g.large"
}

module "opensearch" {
  source = "../../modules/opensearch"

  project_settings = var.project_settings

  subnet_ids = module.network.opensearch_subnet_ids
  security_group_ids = [
    module.security.opensearch_security_group_id
  ]
}

module "dms" {
  source = "../../modules/dms"

  project_settings = var.project_settings

  subnet_ids                 = module.network.dms_subnet_ids
  dms_vpc_security_group_ids = [module.security.dms_security_group_id]

  aurora_server_name = module.aurora_mysql.cluster_endpoint
  aurora_username    = "migration"
  aurora_password    = "Pass1234!"

  opensearch_endpoint   = module.opensearch.domain_endpoint
  opensearch_domain_arn = module.opensearch.domain_arn
}