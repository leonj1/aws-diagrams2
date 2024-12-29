import pytest
from diagrams import Diagram
from diagram_generator import DiagramGenerator, create_diagram


def test_basic_hierarchy():
    """Test diagram generation with basic hierarchy."""
    hierarchy = {
        "aws-cloud": {
            "type": "aws-cloud",
            "name": "AWS Cloud",
            "children": {
                "region": {
                    "type": "region",
                    "name": "AWS Region",
                    "children": {
                        "aws-vpc": {
                            "type": "VPC",
                            "name": "VPC",
                            "children": {}
                        }
                    }
                }
            }
        }
    }
    
    # Should not raise any exceptions
    create_diagram(hierarchy, "test_basic")


def test_full_hierarchy():
    """Test diagram generation with full ECS hierarchy."""
    hierarchy = {
        "aws-cloud": {
            "type": "aws-cloud",
            "name": "AWS Cloud",
            "children": {
                "region": {
                    "type": "region",
                    "name": "AWS Region",
                    "children": {
                        "aws-vpc": {
                            "type": "VPC",
                            "name": "VPC",
                            "children": {
                                "aws-subnet": {
                                    "type": "aws-subnet",
                                    "name": "Subnet",
                                    "children": {
                                        "aws-ecs-cluster": {
                                            "type": "aws-ecs-cluster",
                                            "name": "ECS Cluster",
                                            "children": {
                                                "aws-ecs-service": {
                                                    "type": "aws-ecs-service",
                                                    "name": "ECS Service",
                                                    "children": {
                                                        "aws-ecs-task-definition": {
                                                            "type": "aws-ecs-task-definition",
                                                            "name": "ECS Task Definition",
                                                            "children": {}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Should not raise any exceptions
    create_diagram(hierarchy, "test_full")


def test_unknown_resource_type():
    """Test handling of unknown resource types."""
    hierarchy = {
        "aws-cloud": {
            "type": "unknown-type",
            "name": "Unknown Resource",
            "children": {}
        }
    }
    
    # Should handle unknown type gracefully
    create_diagram(hierarchy, "test_unknown")


def test_empty_hierarchy():
    """Test handling of empty hierarchy."""
    hierarchy = {}
    
    # Should handle empty hierarchy gracefully
    create_diagram(hierarchy, "test_empty")


def test_node_creation():
    """Test node creation for different resource types."""
    with Diagram("Test", show=False):
        generator = DiagramGenerator()
        
        # Test known resource types
        assert generator._create_node(None, "VPC", "Test VPC") is not None
        assert generator._create_node(None, "aws-subnet", "Test Subnet") is not None
        assert generator._create_node(None, "aws-ecs-cluster", "Test Cluster") is not None
        
        # Test unknown resource type
        assert generator._create_node(None, "unknown-type", "Test Unknown") is None


def test_hierarchy_processing():
    """Test hierarchy processing logic."""
    generator = DiagramGenerator()
    
    # Test simple parent-child relationship
    hierarchy = {
        "type": "VPC",
        "name": "Parent VPC",
        "children": {
            "subnet": {
                "type": "aws-subnet",
                "name": "Child Subnet",
                "children": {}
            }
        }
    }
    
    with Diagram(
        name="Test Diagram",
        filename="test_processing",
        show=False
    ):
        # Should process hierarchy without errors
        generator._process_hierarchy(None, hierarchy)
