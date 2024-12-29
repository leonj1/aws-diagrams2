import json
import sys
import os
import argparse
from terraform_reader import get_terraform_contents
from terraform_hierarchy import create_aws_hierarchy
from diagram_generator import create_diagram
from aws_parent_resources import is_parent_resource
from typing import Dict, Any, List, Tuple

def _get_node_class(resource_type: str) -> str:
    """Get the appropriate node class for a resource type."""
    node_map = {
        "aws-cloud": "ManagementAndGovernance",
        "region": "General",
        "VPC": "VPC",
        "aws-route-table": "RouteTable",
        "aws-route-table-association": "RouteTable",
        "aws-subnet": "PrivateSubnet",
        "aws-iam-role": "IAMRole",
        "aws-iam-role-policy-attachment": "IAMRole",
        "aws-security-group": "Nacl",
        "aws-ecs-cluster": "ECS",
        "aws-ecs-service": "ElasticContainerServiceService",
        "aws-ecs-task-definition": "Fargate"
    }
    return node_map.get(resource_type, "General")

def _get_cluster_color(node_type: str) -> str:
    """Get the appropriate background color for a cluster type."""
    # Handle VPC case since it's capitalized in the hierarchy
    if node_type == "VPC":
        node_type = "aws-vpc"
    return can_be_parent.get(node_type, "#F5F5F5")  # Default to light gray

def _process_node(node_data: Dict[str, Any], indent: int = 1) -> Tuple[List[str], List[str]]:
    """Process a node in the hierarchy and return its script lines and variable declarations."""
    lines = []
    vars = []
    indent_str = "    " * indent
    
    # Handle root level node
    if "aws-cloud" in node_data:
        node = node_data["aws-cloud"]
    else:
        node = node_data
    
    # Get node type and convert to AWS resource format
    node_type = node.get("type", "")
    
    # Handle special cases and parent resources
    if node_type in ["aws-cloud", "region"]:
        # Process cloud and region children
        if "children" in node:
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent)
                lines.extend(child_lines)
                vars.extend(child_vars)
        return lines, vars
    elif node_type == "VPC":
        # VPC is always a cluster
        is_cluster = True
    elif node_type == "aws-ecs-service":
        # ECS Service is always a cluster to contain task definitions
        is_cluster = True
    else:
        # Convert type to AWS resource format (e.g., "aws-ecs-cluster" -> "aws_ecs_cluster")
        resource_type = f"aws_{node_type.lower().replace('-', '_')}"
        is_cluster = is_parent_resource(resource_type)
    
    if is_cluster:
        lines.append(f"{indent_str}with Cluster(")
        lines.append(f'{indent_str}    "{node["name"]} ({node["type"]})",')
        # Get cluster color based on node type
        cluster_color = _get_cluster_color(node["type"])
        lines.append(f"{indent_str}    graph_attr={{")
        lines.append(f'{indent_str}        "style": "rounded",')
        lines.append(f'{indent_str}        "bgcolor": "{cluster_color}",')
        lines.append(f'{indent_str}        "pencolor": "#666666",')
        lines.append(f'{indent_str}        "penwidth": "2.0",')
        lines.append(f'{indent_str}        "fontsize": "12",')
        lines.append(f'{indent_str}        "margin": "15"')
        lines.append(f"{indent_str}    }}")
        lines.append(f"{indent_str}):")
        
        # Create node (except for ECS services which are pure clusters)
        if node["type"] != "aws-ecs-service":
            var_name = f"{node['type'].lower().replace('-', '_')}_{len(vars)}"
            node_class = _get_node_class(node["type"])
            lines.append(f'{indent_str}    {var_name} = {node_class}("{node["name"]}")')
            vars.append(var_name)
        
        # Process children (with special handling for ECS service)
        if "children" in node:
            child_vars_by_type = {}
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent + 1)
                lines.extend(child_lines)
                child_type = child["type"]
                if child_type not in child_vars_by_type:
                    child_vars_by_type[child_type] = []
                child_vars_by_type[child_type].extend(child_vars)
            
            # Add connections
            for child_type, child_vars in child_vars_by_type.items():
                if len(child_vars) > 1:
                    for i in range(len(child_vars) - 1):
                        lines.append(f"{indent_str}    {child_vars[i]} >> {child_vars[i+1]}")
                if child_vars and node["type"] != "aws-ecs-service":
                    lines.append(f"{indent_str}    {var_name} >> {child_vars[0]}")
    else:
        # Create regular node
        var_name = f"{node['type'].lower().replace('-', '_')}_{len(vars)}"
        node_class = _get_node_class(node["type"])
        lines.append(f'{indent_str}{var_name} = {node_class}("{node["name"]}")')
        vars.append(var_name)
        
        # Process children
        if "children" in node:
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent)
                lines.extend(child_lines)
                if child_vars:
                    lines.append(f"{indent_str}{var_name} >> {child_vars[0]}")
                    vars.extend(child_vars)
    
    return lines, vars

can_be_parent = {
    "aws-cloud": "#F5F5F5",     # Light gray
    "region": "#F5F5F5",        # Light gray
    "aws-vpc": "#E8F4FA",       # Light blue
    "aws-subnet": "#E6FFE6",    # Light green
    "aws-ecs-cluster": "#FFF0E6", # Light orange
    "aws-ecs-service": "#F5E6FF"  # Light purple
}

def create_diagram_script(hierarchy_json: str, output_filename: str = "aws_architecture") -> str:
    """
    Create a Python script that uses mingrammer diagrams to render AWS architecture.
    
    Args:
        hierarchy_json (str): JSON string containing AWS resource hierarchy
        
    Returns:
        str: Python script that will generate the diagram
    """
    # Parse hierarchy JSON
    hierarchy = json.loads(hierarchy_json)
    
    # Generate script lines
    script_lines = [
        "#!/usr/bin/env python3",
        "from diagrams import Diagram, Cluster",
        "from diagrams.aws.compute import ECS, ElasticContainerServiceService, Fargate",
        "from diagrams.aws.network import VPC, RouteTable, PrivateSubnet, InternetGateway, NATGateway, Nacl",
        "from diagrams.aws.security import IAMRole, IAM",
        "from diagrams.aws.general import General",
        "from diagrams.aws.management import ManagementAndGovernance",
        "",
        "# Create diagram",
        'with Diagram(',
        '    "AWS Architecture",',
        f'    filename="{output_filename}",',
        '    show=False,',
        '    direction="TB",',
        "    graph_attr={",
        '        "splines": "ortho",     # Orthogonal connections',
        '        "nodesep": "1.0",       # Node separation',
        '        "ranksep": "2.0",       # Rank separation',
        '        "pad": "2.5",           # Padding',
        '        "concentrate": "true",   # Merge parallel edges',
        '        "compound": "true",      # Enable cluster connections',
        '        "rankdir": "TB",        # Top to bottom direction',
        '        "ordering": "out"       # Maintain order of connections',
        "    },",
        "    node_attr={",
        '        "fontsize": "12",       # Node label font size',
        '        "margin": "1.2",        # Significantly increased margin for label spacing',
        '        "height": "1.2",        # Node height',
        '        "width": "1.8",         # Node width',
        '        "labelloc": "b",        # Place label below node',
        '        "imagepos": "tc",       # Image at top-center',
        '        "labeldistance": "3.0", # Increased distance between node and label',
        '        "labelspacing": "2.0",  # Increased space between node and label',
        '        "nodesep": "1.5"        # Increased separation between nodes',
        "    },",
        "    edge_attr={",
        '        "minlen": "2",          # Minimum edge length',
        '        "penwidth": "2.0",      # Edge thickness',
        '        "color": "#666666"      # Edge color',
        "    }",
        "):"
    ]
    
    # Process hierarchy
    node_lines, _ = _process_node(hierarchy)
    
    # Add nodes or pass statement
    if node_lines:
        script_lines.extend(node_lines)
    else:
        script_lines.append("    pass  # No nodes to render")
    
    # Join all lines
    script = "\n".join(script_lines)
    return script

if __name__ == "__main__":
    """
    Main function that:
    1. Takes a folder path and output filename as arguments
    2. Reads all .tf and .tfvars files in the folder
    3. Creates AWS resource hierarchy
    4. Generates architecture diagram
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate AWS architecture diagram from Terraform files"
    )
    parser.add_argument(
        "folder_path",
        help="Path to folder containing Terraform files"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="aws_architecture",
        help="Output filename for diagram (without extension, default: aws_architecture)"
    )
    
    args = parser.parse_args()
    
    # if output has a .png extension, remove it
    if args.output.endswith(".png"):
        print("Removing .png extension from output filename")
        args.output = args.output[:-4]

    try:
        # Read terraform files
        print(f"Reading Terraform files from {args.folder_path}...")
        try:
            terraform_contents = get_terraform_contents(args.folder_path)
            # print the number of lines in terraform_contents
            print(f"Number of lines in terraform_contents: {len(terraform_contents.splitlines())}")
            # save terraform_contents to file
            with open("terraform_contents.txt", "w") as f:
                f.write(terraform_contents)
        except FileNotFoundError as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)

        # Parse contents into hierarchy
        print("Creating AWS resource hierarchy...")
        try:
            hierarchy = create_aws_hierarchy(terraform_contents)
            # save hierarchy to file. Since its json also prety print it
            with open("heirarchy.json", "w") as f:
                json.dump(hierarchy, f)
        except Exception as e:
            print(f"Error parsing terraform contents: {str(e)}", file=sys.stderr)
            sys.exit(1)

        # Generate diagram
        print(f"Generating diagram as {args.output}.png...")
        try:
            script = create_diagram_script(json.dumps(hierarchy), args.output)
            # Save and execute the script
            script_path = "output_diagram_script.py"
            with open(script_path, "w") as f:
                f.write(script)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Execute script
            os.system(f"python3 {script_path}")
        except Exception as e:
            print(f"Error generating diagram: {str(e)}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Done! 🎉")
