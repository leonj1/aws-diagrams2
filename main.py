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
        # "VPC": "VPC",  # VPC is a pure cluster, not a node
        "aws-route-table": "RouteTable",
        "aws-route-table-association": "RouteTable",
        # "aws-subnet": "PrivateSubnet",  # Subnets are pure clusters, not nodes
        "aws-iam-role": "IAMRole",
        "aws-iam-role-policy-attachment": "IAMRole",
        "aws-security-group": "Nacl",
        "aws-ecs-cluster": "ECS",
        "aws-ecs-service": "ElasticContainerServiceService",
        "aws-ecs-task-definition": "Fargate"
    }
    return node_map.get(resource_type, "General")

def is_cluster(resource_type: str) -> bool:
    """Check if a resource type is a cluster by looking it up in the clusters dictionary.
    
    Args:
        resource_type (str): The AWS resource type to check (e.g., 'aws-vpc', 'VPC')
        
    Returns:
        bool: True if the resource type is a cluster, False otherwise
    """
    # Handle VPC case since it's capitalized in the hierarchy
    if resource_type == "VPC":
        resource_type = "aws-vpc"
    return resource_type in clusters

def _get_cluster_color(node_type: str) -> str:
    """Get the appropriate background color for a cluster type."""
    # Handle VPC case since it's capitalized in the hierarchy
    if node_type == "VPC":
        node_type = "aws-vpc"
    return clusters.get(node_type, "#F5F5F5")  # Default to light gray

def _process_node(node_data: Dict[str, Any], indent: int = 1, region: str = None) -> Tuple[List[str], List[str]]:
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
    if node_type == "aws-cloud":
        # Process cloud children
        if "children" in node:
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent, region)
                lines.extend(child_lines)
                vars.extend(child_vars)
        return lines, vars
    
    # Handle region nodes (keys starting with "region-")
    if node_type == "region":
        # Extract region name from node name
        region_name = node["name"].split("(")[-1].strip(")")
        
        # Create region cluster
        lines.append(f"{indent_str}with Cluster(")
        lines.append(f'{indent_str}    "Region: {region_name}",')
        lines.append(f"{indent_str}    graph_attr={{")
        lines.append(f'{indent_str}        "style": "rounded",')
        lines.append(f'{indent_str}        "bgcolor": "{_get_cluster_color("region")}",')
        lines.append(f'{indent_str}        "pencolor": "#666666",')
        lines.append(f'{indent_str}        "penwidth": "2.0",')
        lines.append(f'{indent_str}        "fontsize": "14",')
        lines.append(f'{indent_str}        "margin": "20",')
        lines.append(f'{indent_str}        "rank": "source",')
        lines.append(f'{indent_str}        "constraint": "true",')
        lines.append(f'{indent_str}        "weight": "100",')
        lines.append(f'{indent_str}        "minlen": "4",')
        lines.append(f'{indent_str}        "group": "regions"')
        lines.append(f"{indent_str}    }}")
        lines.append(f"{indent_str}):")
        lines.append(f"{indent_str}    _dummy = General('dummy')  # Region: {region_name}")
        
        # Process region children
        if "children" in node:
            for child in node["children"].values():
                # Extract region from node name
                region_name = node["name"].split("(")[-1].strip(")")
                child_lines, child_vars = _process_node(child, indent + 1, region_name)
                lines.extend(child_lines)
                vars.extend(child_vars)
        return lines, vars
    
    # Check if this resource is a cluster
    is_cluster_resource = is_cluster(node_type)
    
    if is_cluster_resource:
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
        lines.append(f"{indent_str}    _dummy = General('dummy')  # {node['name']}")
        
        # Process children
        if "children" in node:
            child_vars_by_type = {}
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent + 1, region)
                lines.extend(child_lines)
                child_type = child["type"]
                if child_type not in child_vars_by_type:
                    child_vars_by_type[child_type] = []
                child_vars_by_type[child_type].extend(child_vars)
            
            # Add connections between siblings
            for child_type, child_vars in child_vars_by_type.items():
                if len(child_vars) > 1:
                    for i in range(len(child_vars) - 1):
                        lines.append(f"{indent_str}    {child_vars[i]} >> {child_vars[i+1]}")
    else:
        # Create regular node with region-specific name
        region_suffix = region.replace("-", "_")
        var_name = f"{node['type'].lower().replace('-', '_')}_{region_suffix}_{len(vars)}"
        node_class = _get_node_class(node["type"])
        lines.append(f'{indent_str}{var_name} = {node_class}("{node["name"]}")')
        vars.append(var_name)
        
        # Process children
        if "children" in node:
            for child in node["children"].values():
                child_lines, child_vars = _process_node(child, indent, region)
                lines.extend(child_lines)
                if child_vars:
                    lines.append(f"{indent_str}{var_name} >> {child_vars[0]}")
                    vars.extend(child_vars)
    
    return lines, vars

clusters = {
    "aws-cloud": "#F5F5F5",     # Light gray
    "region": "#F5F5F5",        # Light gray
    "aws-vpc": "#E8F4FA",       # Light blue
    "Subnet": "#E6FFE6",    # Light green
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
        "from diagrams import Diagram, Cluster, Edge",
        "from diagrams.aws.compute import ECS, ElasticContainerServiceService, Fargate",
        "from diagrams.aws.network import RouteTable, InternetGateway, NATGateway, Nacl",
        "from diagrams.aws.security import IAMRole, IAM",
        "from diagrams.aws.general import General",
        "from diagrams.aws.management import ManagementAndGovernance",
        "",
        "# Create diagram",
        "graph_attr = {",
        '    "splines": "ortho",        # Orthogonal connections',
        '    "nodesep": "2.0",          # Node separation',
        '    "ranksep": "40.0",         # Large rank separation for vertical layout',
        '    "pad": "3.0",              # Padding',
        '    "concentrate": "true",      # Merge parallel edges',
        '    "compound": "true",         # Enable cluster connections',
        '    "rankdir": "TB",           # Top to bottom direction',
        '    "ordering": "out",         # Maintain order of connections',
        '    "newrank": "true",         # Enable new ranking mode for better cluster layout',
        '    "clusterrank": "global",   # Force global ranking',
        '    "pack": "false",           # Disable automatic packing',
        '    "overlap": "false",        # Prevent node overlap',
        '    "outputorder": "nodesfirst",# Process nodes before edges',
        '    "sep": "+90",              # Increase separation between all elements',
        '    "esep": "+85",             # Increase edge separation',
        '    "margin": "7.0",           # Add margin around the graph',
        '    "constraint": "true",      # Enable constraint-based layout',
        '    "forcelabels": "true",    # Force label placement',
        '    "remincross": "true",     # Minimize edge crossings',
        '    "layout": "dot",         # Use dot layout engine',
        '    "mindist": "5.0",        # Minimum distance between nodes',
        '    "mode": "ipsep"         # Use constrained layout mode',
        "}",
        "",
        "node_attr = {",
        '    "fontsize": "12",       # Node label font size',
        '    "margin": "1.5",        # Significantly increased margin for label spacing',
        '    "height": "1.5",        # Node height',
        '    "width": "2.0",         # Node width',
        '    "labelloc": "b",        # Place label below node',
        '    "imagepos": "tc",       # Image at top-center',
        '    "labeldistance": "3.0", # Increased distance between node and label',
        '    "labelspacing": "2.0",  # Increased space between node and label',
        '    "nodesep": "1.5"        # Increased separation between nodes',
        "}",
        "",
        "edge_attr = {",
        '    "minlen": "2",          # Minimum edge length',
        '    "penwidth": "2.0",      # Edge thickness',
        '    "color": "#666666"      # Edge color',
        "}",
        "",
        "",
    ]
    
    # Process hierarchy and prepare node lines
    node_lines, _ = _process_node(hierarchy)
    
    # No need for invisible edges with updated graph attributes
    region_edges = []
    
    # Add diagram creation
    script_lines.append("def create_diagram():")
    script_lines.append('    with Diagram(')
    script_lines.append('        "AWS Architecture",')
    script_lines.append(f'        filename="{output_filename}",')
    script_lines.append('        show=False,')
    script_lines.append('        direction="TB",')
    script_lines.append('        graph_attr=graph_attr,')
    script_lines.append('        node_attr=node_attr,')
    script_lines.append('        edge_attr=edge_attr')
    script_lines.append('    ) as diagram:')
    # Add nodes with proper indentation
    if node_lines:
        # Adjust indentation for all node lines
        node_lines = ['        ' + line for line in node_lines]
        script_lines.extend(node_lines)
        script_lines.extend(region_edges)
    else:
        script_lines.append('        pass')
    script_lines.append("")
    script_lines.append("if __name__ == '__main__':")
    script_lines.append("    create_diagram()")
    script_lines.append("")
    
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
