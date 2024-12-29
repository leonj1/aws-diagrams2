import json
import pytest
from terraform_hierarchy import create_aws_hierarchy, format_hierarchy


def test_empty_terraform():
    """Test hierarchy creation with empty terraform content."""
    result = create_aws_hierarchy("")
    assert "aws-cloud" in result
    assert "region" in result["aws-cloud"]["children"]
    assert result["aws-cloud"]["children"]["region"]["children"] == {}


def test_basic_vpc():
    """Test hierarchy creation with a basic VPC resource."""
    content = '''
================
File: main.tf
================
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
'''
    result = create_aws_hierarchy(content)
    
    # Verify basic structure
    assert "aws-cloud" in result
    assert "region" in result["aws-cloud"]["children"]
    region_children = result["aws-cloud"]["children"]["region"]["children"]
    
    # Verify VPC
    assert "aws-vpc" in region_children
    assert region_children["aws-vpc"]["name"] == "VPC"
    assert region_children["aws-vpc"]["type"] == "VPC"


def test_full_ecs_structure():
    """Test hierarchy creation with a full ECS infrastructure."""
    content = '''
================
File: ecs.tf
================
resource "aws_ecs_cluster" "main" {
  name = "react-cluster"
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "react_app" {
  family                   = "react-app"
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = 256
  memory                  = 512
  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "react-app"
      image     = "react-hello-world:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
    }
  ])
}

================
File: network.tf
================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ecs-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "ecs-public-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ecs-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "ecs-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

================
File: service.tf
================
resource "aws_security_group" "react_service" {
  name        = "react-service-sg"
  description = "Security group for React ECS service"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_service" "react_app" {
  name            = "react-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.react_app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.react_service.id]
    assign_public_ip = true
  }
}
'''
    result = create_aws_hierarchy(content)
    
    # Get references to nested structures
    region_children = result["aws-cloud"]["children"]["region"]["children"]
    vpc_children = region_children["aws-vpc"]["children"]
    subnet_children = vpc_children["aws-subnet"]["children"]
    cluster_children = subnet_children["aws-ecs-cluster"]["children"]
    service_children = cluster_children["aws-ecs-service"]["children"]
    
    # Verify VPC level resources
    assert "aws-route-table" in vpc_children
    assert "aws-route-table-association" in vpc_children
    assert "aws-iam-role" in vpc_children
    assert "aws-iam-role-policy-attachment" in vpc_children
    assert "aws-security-group" in vpc_children
    assert "aws-subnet" in vpc_children
    
    # Verify resource names
    assert vpc_children["aws-route-table"]["name"] == "Route Table"
    assert vpc_children["aws-route-table-association"]["name"] == "Route Table Association"
    assert vpc_children["aws-iam-role"]["name"] == "IAM Role"
    assert vpc_children["aws-iam-role-policy-attachment"]["name"] == "IAM Role Policy Attachment"
    assert vpc_children["aws-security-group"]["name"] == "AWS Security Group"
    assert vpc_children["aws-subnet"]["name"] == "subnet"
    
    # Verify ECS resources and names
    assert "aws-ecs-cluster" in subnet_children
    assert subnet_children["aws-ecs-cluster"]["name"] == "ECS Cluster"
    
    assert "aws-ecs-service" in cluster_children
    assert cluster_children["aws-ecs-service"]["name"] == "ECS Service"
    
    assert "aws-ecs-task-definition" in service_children
    assert service_children["aws-ecs-task-definition"]["name"] == "ECS Task Definition"


def test_format_hierarchy():
    """Test the format_hierarchy function."""
    hierarchy = {
        "test": {
            "name": "Test",
            "children": {}
        }
    }
    
    # Test with default indentation
    formatted = format_hierarchy(hierarchy)
    assert isinstance(formatted, str)
    parsed = json.loads(formatted)
    assert parsed == hierarchy
    
    # Test with custom indentation
    formatted = format_hierarchy(hierarchy, indent=4)
    assert isinstance(formatted, str)
    parsed = json.loads(formatted)
    assert parsed == hierarchy


def test_multiple_files():
    """Test hierarchy creation with resources spread across multiple files."""
    content = '''
================
File: vpc.tf
================
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

================
File: ecs.tf
================
resource "aws_ecs_cluster" "main" {
  name = "app-cluster"
}

================
File: security.tf
================
resource "aws_security_group" "app" {
  vpc_id = aws_vpc.main.id
}
'''
    result = create_aws_hierarchy(content)
    
    # Verify resources from different files are properly organized
    region_children = result["aws-cloud"]["children"]["region"]["children"]
    vpc_children = region_children["aws-vpc"]["children"]
    
    # Verify security group is under VPC
    assert "aws-security-group" in vpc_children
    assert vpc_children["aws-security-group"]["name"] == "AWS Security Group"
    assert vpc_children["aws-security-group"]["type"] == "aws-security-group"
    
    # Verify ECS cluster is at the VPC level since no subnet is defined
    assert "aws-ecs-cluster" in vpc_children
    assert vpc_children["aws-ecs-cluster"]["name"] == "ECS Cluster"
    assert vpc_children["aws-ecs-cluster"]["type"] == "aws-ecs-cluster"
