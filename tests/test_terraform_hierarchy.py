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
File: vpc.tf
================
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

================
File: ecs.tf
================
resource "aws_ecs_cluster" "main" {
  name = "app-cluster"
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs-task-execution-role"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "app" {
  family = "app"
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
}

resource "aws_security_group" "app" {
  vpc_id = aws_vpc.main.id
}

resource "aws_ecs_service" "app" {
  name = "app"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
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
    
    # Verify ECS resources
    assert "aws-ecs-cluster" in subnet_children
    assert "aws-ecs-service" in cluster_children
    assert "aws-ecs-task-definition" in service_children


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
