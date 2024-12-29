from typing import Dict, Any
from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS, ElasticContainerServiceService, Fargate
from diagrams.aws.network import VPC, RouteTable, PrivateSubnet, InternetGateway, NATGateway, Nacl
from diagrams.aws.security import IAMRole, IAM
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
            "aws-route-table-association": RouteTable,
            "aws-subnet": PrivateSubnet,
            "aws-iam-role": IAMRole,
            "aws-iam-role-policy-attachment": IAMRole,
            "aws-security-group": Nacl,  # Using NACL icon for security group
            "aws-ecs-cluster": ECS,
            "aws-ecs-service": ElasticContainerServiceService,
            "aws-ecs-task-definition": Fargate  # Using Fargate icon for task definition
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
        resource_type = data.get("type")
        resource_name = data.get("name", "")
        
        # Skip cloud and region nodes as they're just containers
        if resource_type in ["aws-cloud", "region"]:
            children = data.get("children", {})
            for child_name, child_data in children.items():
                self._process_hierarchy(graph, child_data, parent_node)
            return None
        
        # Create clusters for grouping resources
        if resource_type in ["VPC", "aws-subnet"]:
            with Cluster(
                f"{resource_name} ({resource_type})",
                graph_attr={
                    "style": "rounded",
                    "bgcolor": "lightgrey",
                    "pencolor": "#336699",
                    "penwidth": "2.0",
                    "fontsize": "12",
                    "margin": "15"
                }
            ):
                # Create the main node
                current_node = self._create_node(graph, resource_type, resource_name)
                if not current_node:
                    return None
                
                # Process children within cluster
                children = data.get("children", {})
                child_nodes = []
                
                # Group similar resources
                resource_groups = {}
                for child_name, child_data in children.items():
                    child_type = child_data.get("type", "")
                    if child_type not in resource_groups:
                        resource_groups[child_type] = []
                    resource_groups[child_type].append(child_data)
                
                # Process each resource group
                for group_type, group_data in resource_groups.items():
                    group_nodes = []
                    with Cluster(
                        group_type,
                        graph_attr={
                            "style": "dashed",
                            "bgcolor": "white",
                            "pencolor": "#666666",
                            "penwidth": "1.0",
                            "fontsize": "10",
                            "margin": "10",
                            "label": f"{group_type} Resources"
                        }
                    ):
                        for child_data in group_data:
                            child_node = self._process_hierarchy(graph, child_data, current_node)
                            if child_node:
                                group_nodes.append(child_node)
                    child_nodes.extend(group_nodes)
                
                # Connect nodes within groups
                for i in range(len(child_nodes) - 1):
                    if child_nodes[i] and child_nodes[i+1]:
                        child_nodes[i] >> child_nodes[i+1]
                
                return current_node
        else:
            # Create regular node
            current_node = self._create_node(graph, resource_type, resource_name)
            if not current_node:
                return None
            
            # Process children
            children = data.get("children", {})
            for child_name, child_data in children.items():
                child_node = self._process_hierarchy(graph, child_data, current_node)
                if current_node and child_node:
                    current_node >> child_node
            
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
            direction="TB",  # Top to bottom layout
            graph_attr={
                "splines": "ortho",     # Orthogonal connections
                "nodesep": "1.0",       # Further increased node separation
                "ranksep": "2.0",       # Further increased rank separation
                "pad": "2.5",           # Further increased padding
                "concentrate": "true",   # Merge parallel edges
                "compound": "true",      # Enable cluster connections
                "rankdir": "TB",        # Top to bottom direction
                "ordering": "out"       # Maintain order of connections
            },
            node_attr={
                "fontsize": "12",       # Node label font size
                "margin": "0.4",        # Increased node margin
                "height": "1.2",        # Node height
                "width": "1.8"          # Node width
            },
            edge_attr={
                "minlen": "2",          # Minimum edge length
                "penwidth": "2.0",      # Edge thickness
                "color": "#666666"      # Edge color
            }
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
