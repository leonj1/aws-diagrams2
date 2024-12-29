from typing import Dict, Any
from diagrams import Diagram
from diagrams.aws.compute import ECS, ElasticContainerServiceService
from diagrams.aws.network import VPC, RouteTable, PrivateSubnet, InternetGateway, Nacl
from diagrams.aws.security import IAMRole
from diagrams.aws.general import General
from diagrams.aws.management import ManagementAndGovernance



class DiagramGenerator:
    """Generator for AWS architecture diagrams from JSON hierarchy."""
    
    def __init__(self):
        # Map AWS resource types to diagram node classes
        self.node_map = {
            "aws-cloud": ManagementAndGovernance,
            "region": General,
            "VPC": VPC,
            "aws-route-table": RouteTable,
            "aws-subnet": PrivateSubnet,
            "aws-iam-role": IAMRole,
            "aws-security-group": Nacl,  # Using NACL icon for security group
            "aws-ecs-cluster": ECS,
            "aws-ecs-service": ElasticContainerServiceService,
            "aws-ecs-task-definition": ECS  # Using ECS icon for task definition
        }
    
    def _create_node(self, graph, resource_type: str, name: str):
        """
        Create a diagram node for the given resource type.
        
        Args:
            graph: Current diagram context
            resource_type (str): Type of AWS resource
            name (str): Name to display for the resource
            
        Returns:
            Node: Created diagram node
        """
        node_class = self.node_map.get(resource_type)
        if node_class:
            return node_class(name)
        return None
    
    def _process_hierarchy(self, graph, data: Dict[str, Any], parent_node=None):
        """
        Recursively process the hierarchy and create nodes and connections.
        
        Args:
            graph: Current diagram context
            data (Dict[str, Any]): Current level of hierarchy
            parent_node: Parent node to connect to (if any)
        
        Returns:
            Node: Created node for current level
        """
        # Create node for current level
        current_node = self._create_node(graph, data.get("type"), data.get("name"))
        
        # Connect to parent if both exist
        if parent_node and current_node:
            parent_node >> current_node
        
        # Process children
        children = data.get("children", {})
        for child_name, child_data in children.items():
            self._process_hierarchy(graph, child_data, current_node)
        
        return current_node
    
    def generate(self, hierarchy: Dict[str, Any], filename: str = "aws_architecture"):
        """
        Generate AWS architecture diagram from hierarchy.
        
        Args:
            hierarchy (Dict[str, Any]): AWS resource hierarchy
            filename (str): Output filename (without extension)
        """
        # Create diagram context
        with Diagram(
            name="AWS Architecture",
            filename=filename,
            show=False,  # Don't show diagram immediately
            direction="TB"  # Top to bottom layout
        ):
            # Process hierarchy starting from root
            self._process_hierarchy(None, hierarchy)


def create_diagram(hierarchy: Dict[str, Any], filename: str = "aws_architecture"):
    """
    Create AWS architecture diagram from hierarchy.
    
    Args:
        hierarchy (Dict[str, Any]): AWS resource hierarchy
        filename (str): Output filename (without extension)
    """
    generator = DiagramGenerator()
    generator.generate(hierarchy, filename)


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) != 2:
        print("Usage: python diagram_generator.py <hierarchy_json_file>")
        sys.exit(1)
    
    # Read hierarchy from JSON file
    with open(sys.argv[1], 'r') as f:
        hierarchy = json.load(f)
    
    # Generate diagram
    create_diagram(hierarchy)
