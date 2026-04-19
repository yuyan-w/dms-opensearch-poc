output "cluster_endpoint" {
  value = module.aurora_mysql.cluster_endpoint
}

output "cluster_reader_endpoint" {
  value = module.aurora_mysql.cluster_reader_endpoint
}

output "cluster_port" {
  value = module.aurora_mysql.cluster_port
}

output "cluster_database_name" {
  value = module.aurora_mysql.cluster_database_name
}