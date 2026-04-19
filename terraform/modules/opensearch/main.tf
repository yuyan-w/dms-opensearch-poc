locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
  domain_name = "${local.name_prefix}-opensearch"
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/opensearch/${local.domain_name}/application"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_resource_policy" "opensearch" {
  policy_name = "${local.domain_name}-log-policy"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchCloudWatchLogs"
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.application.arn}:*"
      }
    ]
  })
}

module "opensearch" {
  source  = "terraform-aws-modules/opensearch/aws"
  version = "2.5.0"

  domain_name    = local.domain_name
  engine_version = "OpenSearch_2.11"

  create_security_group = false

  advanced_security_options = {
    enabled = false
  }

  cluster_config = {
    instance_type            = "m8g.medium.search"
    instance_count           = 1
    zone_awareness_enabled   = false
    dedicated_master_enabled = false
  }

  ebs_options = {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 20
    iops        = 3000
    throughput  = 125
  }

  vpc_options = {
    subnet_ids         = [var.subnet_ids[0]]
    security_group_ids = var.security_group_ids
  }

  domain_endpoint_options = {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  encrypt_at_rest = {
    enabled = true
  }

  node_to_node_encryption = {
    enabled = true
  }

  log_publishing_options = [
    {
      log_type                 = "ES_APPLICATION_LOGS"
      enabled                  = true
      cloudwatch_log_group_arn = aws_cloudwatch_log_group.application.arn
    }
  ]

  tags = {
    Name    = local.domain_name
    Project = var.project_settings.project
    Env     = var.project_settings.env
  }

  depends_on = [
    aws_cloudwatch_log_group.application,
    aws_cloudwatch_log_resource_policy.opensearch
  ]
}

resource "aws_opensearch_domain_policy" "this" {
  domain_name = module.opensearch.domain_name

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = [
          "es:ESHttpGet",
          "es:ESHttpHead",
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpDelete",
          "es:ESHttpPatch"
        ]
        Resource = "${module.opensearch.domain_arn}/*"
      }
    ]
  })
}