# modules/security/outputs.tf
output "ec2_security_group_id" {
  value = aws_security_group.ec2.id
}

output "aurora_security_group_id" {
  value = aws_security_group.aurora.id
}

output "dms_security_group_id" {
  value = aws_security_group.dms.id
}

output "opensearch_security_group_id" {
  value = aws_security_group.opensearch.id
}