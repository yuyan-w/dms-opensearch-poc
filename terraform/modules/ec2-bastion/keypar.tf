# modules/ec2-bastion/keypair.tf
resource "aws_key_pair" "key" {
  key_name   = "${local.name_prefix}-ec2-key"
  public_key = file("${path.root}/../../../.ssh/id_ed25519_ec2.pub")

  tags = {
    Name = "${local.name_prefix}-ec2-key"
  }
}