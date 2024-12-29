import json
import sys
import argparse
from terraform_reader import get_terraform_contents
from terraform_hierarchy import create_aws_hierarchy
from diagram_generator import create_diagram
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
    
    # Skip cloud and region nodes
    if node.get("type") in ["aws-cloud", "region"]:
        if "children" in node:
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent)
                lines.extend(child_lines)
                vars.extend(child_vars)
        return lines, vars
    
    # Create cluster for VPC and subnet
    if node["type"] in ["VPC", "aws-subnet"]:
        lines.append(f"{indent_str}with Cluster(")
        lines.append(f'{indent_str}    "{node["name"]} ({node["type"]})",')
        lines.append(f"{indent_str}    graph_attr={{")
        lines.append(f'{indent_str}        "style": "rounded",')
        lines.append(f'{indent_str}        "bgcolor": "lightgrey",')
        lines.append(f'{indent_str}        "pencolor": "#336699",')
        lines.append(f'{indent_str}        "penwidth": "2.0",')
        lines.append(f'{indent_str}        "fontsize": "12",')
        lines.append(f'{indent_str}        "margin": "15"')
        lines.append(f"{indent_str}    }}")
        lines.append(f"{indent_str}):")
        
        # Create node
        var_name = f"{node['type'].lower().replace('-', '_')}_{len(vars)}"
        node_class = _get_node_class(node["type"])
        lines.append(f'{indent_str}    {var_name} = {node_class}("{node["name"]}")')
        vars.append(var_name)
        
        # Process children
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
                if child_vars:
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

def create_diagram_script(hierarchy_json: str) -> str:
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
        '        "margin": "0.4",        # Node margin',
        '        "height": "1.2",        # Node height',
        '        "width": "1.8"          # Node width',
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

    try:
        # Read terraform files
        print(f"Reading Terraform files from {args.folder_path}...")
        try:
            terraform_contents = get_terraform_contents(args.folder_path)
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
            # save hierarchy to file
            with open("hierarchy.json", "w") as f:
                json.dump(hierarchy, f)
        except Exception as e:
            print(f"Error parsing terraform contents: {str(e)}", file=sys.stderr)
            sys.exit(1)

        # Generate diagram
        print(f"Generating diagram as {args.output}.png...")
        try:
            script = create_diagram_script(json.dumps(hierarchy))
            # Save and execute the script
            script_path = "output_diagram_script.py"
            with open(script_path, "w") as f:
                f.write(script)
            
            # Make script executable
            import os
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
