import pytest
import json
from main import create_diagram_script


def test_create_diagram_script_empty_hierarchy():
    """Test script generation with empty hierarchy."""
    hierarchy = {
            "aws-cloud": {
                "type": "aws-cloud",
                "name": "AWS Cloud",
                "children": {}
            }
    }
    
    script = create_diagram_script(json.dumps(hierarchy))
    assert "#!/usr/bin/env python3" in script
    assert "from diagrams import Diagram" in script
    assert "AWS Architecture" in script


def test_create_diagram_script_vpc():
    """Test script generation with VPC."""
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
                            "name": "VPC",
                            "type": "VPC",
                            "children": {}
                        }
                    }
                }
            }
        }
    }
    
    script = create_diagram_script(json.dumps(hierarchy))
    assert "VPC(" in script
    assert "Cluster(" in script


def test_create_diagram_script_ecs():
    """Test script generation with ECS resources."""
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
                            "name": "VPC",
                            "type": "VPC",
                            "children": {
                                "aws-ecs-cluster": {
                                    "name": "ECS Cluster",
                                    "type": "aws-ecs-cluster",
                                    "children": {
                                        "aws-ecs-service": {
                                            "name": "ECS Service",
                                            "type": "aws-ecs-service",
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
    
    script = create_diagram_script(json.dumps(hierarchy))
    assert "ECS(" in script
    assert "ElasticContainerServiceService(" in script
    assert ">>" in script  # Check for connections


def test_create_diagram_script_invalid_json():
    """Test script generation with invalid JSON."""
    with pytest.raises(json.JSONDecodeError):
        create_diagram_script("invalid json")


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up any generated files after each test."""
    yield
    import os
    for file in os.listdir():
        if file.endswith(".png"):
            os.remove(file)
