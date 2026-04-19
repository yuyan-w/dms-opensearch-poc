locals {
  name_prefix = "${var.project_settings.project}-${var.project_settings.env}"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

# Public Subnets for EC2 (Bastion)
resource "aws_subnet" "ec2_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.10.0/24"
  availability_zone       = "ap-northeast-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-ec2-subnet-1a"
  }
}

resource "aws_subnet" "ec2_1c" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.11.0/24"
  availability_zone       = "ap-northeast-1c"
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-ec2-subnet-1c"
  }
}

# Aurora Subnets
resource "aws_subnet" "aurora_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.100.0/24"
  availability_zone = "ap-northeast-1a"

  tags = {
    Name = "${local.name_prefix}-aurora-subnet-1a"
  }
}

resource "aws_subnet" "aurora_1c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.101.0/24"
  availability_zone = "ap-northeast-1c"

  tags = {
    Name = "${local.name_prefix}-aurora-subnet-1c"
  }
}

# DMS Subnets
resource "aws_subnet" "dms_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.110.0/24"
  availability_zone = "ap-northeast-1a"

  tags = {
    Name = "${local.name_prefix}-dms-subnet-1a"
  }
}

resource "aws_subnet" "dms_1c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.111.0/24"
  availability_zone = "ap-northeast-1c"

  tags = {
    Name = "${local.name_prefix}-dms-subnet-1c"
  }
}

# OpenSearch Subnets
resource "aws_subnet" "opensearch_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.120.0/24"
  availability_zone = "ap-northeast-1a"

  tags = {
    Name = "${local.name_prefix}-opensearch-subnet-1a"
  }
}

resource "aws_subnet" "opensearch_1c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.121.0/24"
  availability_zone = "ap-northeast-1c"

  tags = {
    Name = "${local.name_prefix}-opensearch-subnet-1c"
  }
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

# Route Table Association for Public Subnets (EC2)
resource "aws_route_table_association" "ec2_1a" {
  subnet_id      = aws_subnet.ec2_1a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "ec2_1c" {
  subnet_id      = aws_subnet.ec2_1c.id
  route_table_id = aws_route_table.public.id
}

# Private Route Table for Aurora
resource "aws_route_table" "aurora" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-aurora-rt"
  }
}

resource "aws_route_table_association" "aurora_1a" {
  subnet_id      = aws_subnet.aurora_1a.id
  route_table_id = aws_route_table.aurora.id
}

resource "aws_route_table_association" "aurora_1c" {
  subnet_id      = aws_subnet.aurora_1c.id
  route_table_id = aws_route_table.aurora.id
}

# Private Route Table for DMS
resource "aws_route_table" "dms" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-dms-rt"
  }
}

resource "aws_route_table_association" "dms_1a" {
  subnet_id      = aws_subnet.dms_1a.id
  route_table_id = aws_route_table.dms.id
}

resource "aws_route_table_association" "dms_1c" {
  subnet_id      = aws_subnet.dms_1c.id
  route_table_id = aws_route_table.dms.id
}

# Private Route Table for OpenSearch
resource "aws_route_table" "opensearch" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-opensearch-rt"
  }
}

resource "aws_route_table_association" "opensearch_1a" {
  subnet_id      = aws_subnet.opensearch_1a.id
  route_table_id = aws_route_table.opensearch.id
}

resource "aws_route_table_association" "opensearch_1c" {
  subnet_id      = aws_subnet.opensearch_1c.id
  route_table_id = aws_route_table.opensearch.id
}
