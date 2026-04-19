# modules/ec2-bastion/outputs.tf
output "instance_id" {
  value = module.ec2.id
}

output "public_ip" {
  value = module.ec2.public_ip
}

output "private_ip" {
  value = module.ec2.private_ip
}