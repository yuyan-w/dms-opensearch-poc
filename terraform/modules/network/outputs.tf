# modules/network/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [
    aws_subnet.ec2_1a.id,
    aws_subnet.ec2_1c.id,
  ]
}

output "aurora_subnet_ids" {
  value = [
    aws_subnet.aurora_1a.id,
    aws_subnet.aurora_1c.id,
  ]
}

output "dms_subnet_ids" {
  value = [
    aws_subnet.dms_1a.id,
    aws_subnet.dms_1c.id,
  ]
}

output "opensearch_subnet_ids" {
  value = [
    aws_subnet.opensearch_1a.id,
    aws_subnet.opensearch_1c.id,
  ]
}