locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
}

resource "aws_cloudwatch_log_group" "dms_task" {
  name              = "/aws/dms/${local.name_prefix}-products-fl-cdc"
  retention_in_days = 7
}

module "dms" {
  source  = "terraform-aws-modules/dms/aws"
  version = "~> 2.0"

  create_iam_roles = true

  repl_subnet_group_name        = "${local.name_prefix}-dms-subnet-group"
  repl_subnet_group_description = "DMS subnet group for ${local.name_prefix}"
  repl_subnet_group_subnet_ids  = var.subnet_ids

  repl_instance_id                          = "${local.name_prefix}-dms"
  repl_instance_class                       = "dms.c6i.large"
  repl_instance_allocated_storage           = 50
  repl_instance_publicly_accessible         = false
  repl_instance_multi_az                    = false
  repl_instance_auto_minor_version_upgrade  = true
  repl_instance_allow_major_version_upgrade = true
  repl_instance_apply_immediately           = true
  repl_instance_vpc_security_group_ids      = var.dms_vpc_security_group_ids

  endpoints = {
    aurora_source = {
      endpoint_id   = "${local.name_prefix}-aurora-source"
      endpoint_type = "source"
      engine_name   = "aurora"

      server_name = var.aurora_server_name
      port        = 3306
      username    = var.aurora_username
      password    = var.aurora_password
      ssl_mode    = "none"

      tags = {
        Name = "${local.name_prefix}-aurora-source"
      }
    }

    opensearch_target = {
      endpoint_id   = "${local.name_prefix}-opensearch-target"
      endpoint_type = "target"
      engine_name   = "elasticsearch"

      elasticsearch_settings = {
        endpoint_uri               = "https://${var.opensearch_endpoint}"
        service_access_role_arn    = aws_iam_role.dms_opensearch_endpoint_role.arn
        error_retry_duration       = 30
        full_load_error_percentage = 10
      }

      tags = {
        Name = "${local.name_prefix}-opensearch-target"
      }
    }
  }

  replication_tasks = {
    products_full_load_cdc = {
      replication_task_id       = "${local.name_prefix}-products-fl-cdc"
      migration_type            = "full-load-and-cdc"
      source_endpoint_key       = "aurora_source"
      target_endpoint_key       = "opensearch_target"
      table_mappings            = file("${path.module}/mapping_products.json")
      replication_task_settings = file("${path.module}/dms_task.json")

      tags = {
        Name = "${local.name_prefix}-products-fl-cdc"
      }
    }
  }

  tags = {
    Terraform   = "true"
    Environment = var.project_settings.env
    Project     = var.project_settings.project
  }
}

resource "aws_iam_role" "dms_opensearch_endpoint_role" {
  name = "${local.name_prefix}-dms-opensearch-endpoint-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "dms.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "dms_opensearch_endpoint_policy" {
  name = "${local.name_prefix}-dms-opensearch-endpoint-policy"
  role = aws_iam_role.dms_opensearch_endpoint_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpDelete",
          "es:ESHttpGet",
          "es:ESHttpHead",
          "es:ESHttpPost",
          "es:ESHttpPut"
        ]
        Resource = [
          var.opensearch_domain_arn,
          "${var.opensearch_domain_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "dms_cdc_latency_target" {
  alarm_name          = "${local.name_prefix}-dms-cdc-latency-target"
  alarm_description   = "DMS CDC latency target is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  threshold           = 60
  period              = 60
  statistic           = "Maximum"
  namespace           = "AWS/DMS"
  metric_name         = "CDCLatencyTarget"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationTaskIdentifier = "${local.name_prefix}-products-fl-cdc"
  }

  alarm_actions = []
  ok_actions    = []
}

resource "aws_cloudwatch_metric_alarm" "dms_cdc_latency_source" {
  alarm_name          = "${local.name_prefix}-dms-cdc-latency-source"
  alarm_description   = "DMS CDC latency source is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  threshold           = 60
  period              = 60
  statistic           = "Maximum"
  namespace           = "AWS/DMS"
  metric_name         = "CDCLatencySource"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationTaskIdentifier = "${local.name_prefix}-products-fl-cdc"
  }

  alarm_actions = []
  ok_actions    = []
}

resource "aws_cloudwatch_metric_alarm" "dms_cpu_utilization" {
  alarm_name          = "${local.name_prefix}-dms-cpu-utilization"
  alarm_description   = "DMS replication instance CPU utilization is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 80
  period              = 300
  statistic           = "Average"
  namespace           = "AWS/DMS"
  metric_name         = "CPUUtilization"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationInstanceIdentifier = "${local.name_prefix}-dms"
  }

  alarm_actions = []
  ok_actions    = []
}

resource "aws_cloudwatch_metric_alarm" "dms_free_memory" {
  alarm_name          = "${local.name_prefix}-dms-free-memory"
  alarm_description   = "DMS replication instance free memory is low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  threshold           = 268435456
  period              = 300
  statistic           = "Minimum"
  namespace           = "AWS/DMS"
  metric_name         = "FreeMemory"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationInstanceIdentifier = "${local.name_prefix}-dms"
  }

  alarm_actions = []
  ok_actions    = []
}

resource "aws_cloudwatch_log_metric_filter" "dms_task_error_count" {
  name           = "${local.name_prefix}-dms-bulk-request-failed"
  log_group_name = "dms-tasks-${local.name_prefix}-dms"

  pattern = "Bulk request failed"
  metric_transformation {
    name      = "${local.name_prefix}-dms-bulk-request-failed"
    namespace = "Custom/DMS"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "dms_task_error_log" {
  alarm_name          = "${local.name_prefix}-dms-task-error-log"
  alarm_description   = "DMS task error detected from CloudWatch Logs"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1
  period              = 60
  statistic           = "Sum"
  namespace           = "Custom/DMS"
  metric_name         = "${local.name_prefix}-dms-task-error-count"
  treat_missing_data  = "notBreaching"

  alarm_actions = []
  ok_actions    = []
}

resource "aws_cloudwatch_dashboard" "dms" {
  dashboard_name = "${local.name_prefix}-dms-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "DMS CDC Latency"
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          stat    = "Maximum"
          period  = 60
          metrics = [
            ["AWS/DMS", "CDCLatencyTarget", "ReplicationTaskIdentifier", "${local.name_prefix}-products-fl-cdc"],
            [".", "CDCLatencySource", ".", "."]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "DMS Instance Resource"
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          stat    = "Average"
          period  = 300
          metrics = [
            ["AWS/DMS", "CPUUtilization", "ReplicationInstanceIdentifier", "${local.name_prefix}-dms"],
            [".", "FreeMemory", ".", ".", { stat = "Minimum", yAxis = "right" }]
          ]
        }
      },
{
  type   = "metric"
  x      = 0
  y      = 6
  width  = 12
  height = 6
  properties = {
    title   = "DMS Bulk Request Failed Count"
    view    = "timeSeries"
    stacked = false
    region  = data.aws_region.current.name
    stat    = "Sum"
    period  = 60
    metrics = [
      ["Custom/DMS", "${local.name_prefix}-dms-bulk-request-failed"]
    ]
  }
}
    ]
  })
}

data "aws_region" "current" {}