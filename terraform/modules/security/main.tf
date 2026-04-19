locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
}

# EC2 (Bastion) Security Group
resource "aws_security_group" "ec2" {
  name        = "${local.name_prefix}-ec2-sg"
  description = "Security group for EC2 bastion host"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-ec2-sg"
  }
}

# Aurora Security Group
resource "aws_security_group" "aurora" {
  name        = "${local.name_prefix}-aurora-sg"
  description = "Security group for Aurora database"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-aurora-sg"
  }
}

# DMS Security Group
resource "aws_security_group" "dms" {
  name        = "${local.name_prefix}-dms-sg"
  description = "Security group for DMS replication instance"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-dms-sg"
  }
}

# OpenSearch Security Group
resource "aws_security_group" "opensearch" {
  name        = "${local.name_prefix}-opensearch-sg"
  description = "Security group for OpenSearch domain"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-opensearch-sg"
  }
}

# EC2 Security Group Rules
resource "aws_security_group_rule" "ec2_ingress_ssh" {
  type              = "ingress"
  from_port         = 50122
  to_port           = 50122
  protocol          = "tcp"
  cidr_blocks       = [var.home_ip]
  security_group_id = aws_security_group.ec2.id
  description       = "SSH from home IP"
}

resource "aws_security_group_rule" "ec2_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ec2.id
  description       = "Allow all outbound traffic"
}

# Aurora Security Group Rules
resource "aws_security_group_rule" "aurora_ingress_ec2" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ec2.id
  security_group_id        = aws_security_group.aurora.id
  description              = "MySQL from EC2"
}

resource "aws_security_group_rule" "aurora_ingress_dms" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.dms.id
  security_group_id        = aws_security_group.aurora.id
  description              = "MySQL from DMS"
}

resource "aws_security_group_rule" "aurora_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.aurora.id
  description       = "Allow all outbound traffic"
}

# DMS Security Group Rules
resource "aws_security_group_rule" "dms_egress_aurora" {
  type                     = "egress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.aurora.id
  security_group_id        = aws_security_group.dms.id
  description              = "Allow to Aurora"
}

resource "aws_security_group_rule" "dms_egress_opensearch" {
  type                     = "egress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.opensearch.id
  security_group_id        = aws_security_group.dms.id
  description              = "Allow to OpenSearch"
}

# OpenSearch Security Group Rules
resource "aws_security_group_rule" "opensearch_ingress_dms" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.dms.id
  security_group_id        = aws_security_group.opensearch.id
  description              = "HTTPS from DMS"
}

resource "aws_security_group_rule" "opensearch_ingress_ec2" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ec2.id
  security_group_id        = aws_security_group.opensearch.id
  description              = "HTTPS from EC2"
}

resource "aws_security_group_rule" "opensearch_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.opensearch.id
  description       = "Allow all outbound traffic"
}
