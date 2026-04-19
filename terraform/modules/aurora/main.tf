locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
}

module "aurora_mysql" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "10.2.0"

  # ========================================
  # 基本設定
  # ========================================
  name           = "${local.name_prefix}-aurora-mysql"
  engine         = "aurora-mysql"
  engine_version = var.engine_version

  database_name               = var.db_name
  manage_master_user_password = false
  master_username             = var.master_username
  master_password_wo          = var.master_password
  master_password_wo_version  = 1

  # ========================================
  # インスタンス構成
  # ========================================
  instances = {
    writer = {
      identifier          = "${local.name_prefix}-aurora-mysql-1"
      instance_class      = var.instance_class
      monitoring_interval = 60
    }
  }

  # ========================================
  # ネットワーク
  # ========================================
  vpc_id                 = var.vpc_id
  vpc_security_group_ids = var.vpc_security_group_ids
  create_security_group  = false

  # サブネットグループを module 内で作成
  create_db_subnet_group = true
  subnets                = var.subnet_ids

  # ========================================
  # パラメータグループ（空で定義）
  # ========================================
  cluster_parameter_group = {
    name        = "${local.name_prefix}-aurora-cluster-pg"
    family      = "aurora-mysql8.0"
    description = "Cluster parameter group for ${local.name_prefix}"

    parameters = [
      {
        name         = "binlog_format"
        value        = "ROW"
        apply_method = "pending-reboot"
      },
      {
        name         = "binlog_row_image"
        value        = "FULL"
        apply_method = "pending-reboot"
      }
    ]
  }

  db_parameter_group = {
    name        = "${local.name_prefix}-aurora-instance-pg"
    family      = "aurora-mysql8.0"
    description = "Instance parameter group for ${local.name_prefix}"

    parameters = []
  }

  # ========================================
  # 運用設定（検証向け）
  # ========================================
  apply_immediately   = true
  deletion_protection = false
  skip_final_snapshot = true

  backup_retention_period      = var.backup_retention_period
  preferred_backup_window      = var.preferred_backup_window
  preferred_maintenance_window = var.preferred_maintenance_window

  storage_encrypted                   = true
  iam_database_authentication_enabled = false


  # ========================================
  # タグ
  # ========================================
  tags = {
    Name = "${local.name_prefix}-aurora-mysql"
    Role = "database"
  }
}