output "replication_instance_arn" {
  value = module.dms.replication_instance_arn
}

output "replication_tasks" {
  value = module.dms.replication_tasks
}

output "endpoints" {
  value = module.dms.endpoints
}