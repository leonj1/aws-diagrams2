import pytest
from terraform_parser import parse_terraform_resources, parse_terraform_files
from resource_node import ResourceNode


# Test cases for parse_terraform_resources
@pytest.mark.parametrize("test_id, content, expected", [
    (
        "single_vpc",
        '''
        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
        }
        ''',
        [
            ResourceNode(
                name="main",
                identifier="aws_vpc.main",
                is_parent=True
            )
        ]
    ),
    (
        "multiple_resources",
        '''
        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
        }
        resource "aws_subnet" "public" {
          vpc_id = aws_vpc.main.id
          cidr_block = "10.0.1.0/24"
        }
        resource "aws_security_group" "web" {
          name = "web"
          vpc_id = aws_vpc.main.id
        }
        ''',
        [
            ResourceNode(
                name="main",
                identifier="aws_vpc.main",
                is_parent=True
            ),
            ResourceNode(
                name="public",
                identifier="aws_subnet.public",
                is_parent=True
            ),
            ResourceNode(
                name="web",
                identifier="aws_security_group.web",
                is_parent=False
            )
        ]
    ),
    (
        "empty_content",
        "",
        []
    ),
    (
        "no_resources",
        '''
        variable "region" {
          default = "us-west-2"
        }
        ''',
        []
    ),
    (
        "complex_resource",
        '''
        resource "aws_ecs_service" "app" {
          name            = "my-app"
          cluster         = aws_ecs_cluster.main.id
          task_definition = aws_ecs_task_definition.app.arn
          desired_count   = 1
          
          network_configuration {
            subnets = aws_subnet.private[*].id
            security_groups = [aws_security_group.app.id]
          }
          
          load_balancer {
            target_group_arn = aws_lb_target_group.app.arn
            container_name   = "app"
            container_port   = 80
          }
        }
        ''',
        [
            ResourceNode(
                name="app",
                identifier="aws_ecs_service.app",
                is_parent=True
            )
        ]
    )
])
def test_parse_terraform_resources(test_id, content, expected):
    """Table-driven tests for parse_terraform_resources function."""
    result = parse_terraform_resources(content)
    
    assert len(result) == len(expected), \
        f"Test {test_id}: Expected {len(expected)} resources, got {len(result)}"
    
    for res, exp in zip(result, expected):
        assert res.name == exp.name, \
            f"Test {test_id}: Expected name {exp.name}, got {res.name}"
        assert res.identifier == exp.identifier, \
            f"Test {test_id}: Expected identifier {exp.identifier}, got {res.identifier}"
        assert res.is_parent == exp.is_parent, \
            f"Test {test_id}: Expected is_parent {exp.is_parent}, got {res.is_parent}"


# Test cases for parse_terraform_files
@pytest.mark.parametrize("test_id, content, expected", [
    (
        "single_file",
        '''================
File: main.tf
================
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
''',
        [
            ResourceNode(
                name="main",
                identifier="aws_vpc.main",
                is_parent=True
            )
        ]
    ),
    (
        "multiple_files",
        '''================
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
resource "aws_ecs_service" "app" {
  name = "app-service"
  cluster = aws_ecs_cluster.main.id
}
''',
        [
            ResourceNode(
                name="main",
                identifier="aws_vpc.main",
                is_parent=True
            ),
            ResourceNode(
                name="main",
                identifier="aws_ecs_cluster.main",
                is_parent=True
            ),
            ResourceNode(
                name="app",
                identifier="aws_ecs_service.app",
                is_parent=True
            )
        ]
    ),
    (
        "empty_files",
        '''================
File: variables.tf
================
variable "region" {
  default = "us-west-2"
}

================
File: outputs.tf
================
output "vpc_id" {
  value = aws_vpc.main.id
}
''',
        []
    ),
    (
        "mixed_content",
        '''================
File: main.tf
================
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

variable "environment" {
  default = "prod"
}

================
File: security.tf
================
resource "aws_security_group" "web" {
  name = "web"
  vpc_id = aws_vpc.main.id
}
''',
        [
            ResourceNode(
                name="main",
                identifier="aws_vpc.main",
                is_parent=True
            ),
            ResourceNode(
                name="web",
                identifier="aws_security_group.web",
                is_parent=False
            )
        ]
    )
])
def test_parse_terraform_files(test_id, content, expected):
    """Table-driven tests for parse_terraform_files function."""
    result = parse_terraform_files(content)
    
    assert len(result) == len(expected), \
        f"Test {test_id}: Expected {len(expected)} resources, got {len(result)}"
    
    for res, exp in zip(result, expected):
        assert res.name == exp.name, \
            f"Test {test_id}: Expected name {exp.name}, got {res.name}"
        assert res.identifier == exp.identifier, \
            f"Test {test_id}: Expected identifier {exp.identifier}, got {res.identifier}"
        assert res.is_parent == exp.is_parent, \
            f"Test {test_id}: Expected is_parent {exp.is_parent}, got {res.is_parent}"


def test_malformed_file_markers():
    """Test handling of malformed file markers."""
    content = '''
Some random content
================
Incomplete marker
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
'''
    result = parse_terraform_files(content)
    assert len(result) == 0, "Expected no resources from malformed content"


def test_nested_blocks():
    """Test parsing resources with nested blocks."""
    content = '''
    resource "aws_security_group" "complex" {
      name = "complex"
      
      ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        
        cidr_blocks = ["0.0.0.0/0"]
      }
      
      egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        
        cidr_blocks = ["0.0.0.0/0"]
      }
      
      tags = {
        Name = "complex"
        Environment = "prod"
      }
    }
    '''
    result = parse_terraform_resources(content)
    assert len(result) == 1
    assert result[0].name == "complex"
    assert result[0].identifier == "aws_security_group.complex"
    assert not result[0].is_parent
