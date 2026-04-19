# modules/ec2-bastion/main.tf
locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
}

data "aws_ami" "amazon_linux_2023" {
  count       = var.ami_id == null ? 1 : 0
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 6.0"

  name = "${local.name_prefix}-bastion"

  ami           = var.ami_id != null ? var.ami_id : data.aws_ami.amazon_linux_2023[0].id
  instance_type = var.instance_type
  key_name      = aws_key_pair.key.key_name
  monitoring    = true

  create_security_group = false

  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.vpc_security_group_ids
  private_ip             = var.private_ip

  associate_public_ip_address = true

  root_block_device = {
    encrypted   = true
    volume_type = "gp3"
    volume_size = 20
    throughput  = 125
    iops        = 3000
  }


  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf update -y
    dnf install -y mariadb105
    # sudo dnf install -y python3-pip

    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

    if grep -qE '^[#[:space:]]*Port[[:space:]]+' /etc/ssh/sshd_config; then
      sed -i 's/^[#[:space:]]*Port[[:space:]].*/Port 50122/' /etc/ssh/sshd_config
    else
      echo 'Port 50122' >> /etc/ssh/sshd_config
    fi

    restorecon -Rv /etc/ssh || true
    systemctl restart sshd
    systemctl enable sshd
  EOF

  tags = {
    Name = "${local.name_prefix}-bastion"
    Role = "bastion"
  }
}