import json
from typing import Dict, Any
from terraform_parser import parse_terraform_files


def create_aws_hierarchy(terraform_content: str) -> Dict[str, Any]:
    """
    Create a hierarchical JSON structure from terraform content showing AWS resource relationships.
    
    Args:
        terraform_content (str): String containing terraform configuration with file markers
        
    Returns:
        Dict[str, Any]: Hierarchical JSON structure of AWS resources
    """
    # Parse terraform content into providers and ResourceNodes
    providers, resources = parse_terraform_files(terraform_content)
    
    # Create base hierarchy structure
    hierarchy = {
        "aws-cloud": {
            "type": "aws-cloud",
            "name": "AWS Cloud",
            "children": {}
        }
    }
    
    # Create a region node for each provider
    cloud_children = hierarchy["aws-cloud"]["children"]
    region_children = {}
    
    # Sort providers by region to ensure consistent ordering
    for provider_alias, region in sorted(providers.items(), key=lambda x: x[1]):
        region_key = f"region-{region}"
        if region_key not in cloud_children:
            cloud_children[region_key] = {
                "type": "region",
                "name": f"AWS Region ({region})",
                "children": {}
            }
        region_children[region] = cloud_children[region_key]["children"]
        
        # Initialize VPC structure for each region
        region_children[region]["aws-vpc"] = {
            "name": f"VPC ({region})",
            "type": "VPC",
            "children": {}
        }
    
    # Process resources by region
    for region in region_children:
        vpc_children = region_children[region]["aws-vpc"]["children"]
        
        # Add VPC-level resources for this region
        resource_types = [
            ("aws-route-table", "Route Table", "aws_route_table."),
            ("aws-route-table-association", "Route Table Association", "aws_route_table_association."),
            ("aws-iam-role", "IAM Role", "aws_iam_role."),
            ("aws-iam-role-policy-attachment", "IAM Role Policy Attachment", "aws_iam_role_policy_attachment."),
            ("aws-security-group", "AWS Security Group", "aws_security_group."),
        ]
        
        for type_key, display_name, prefix in resource_types:
            matching_resources = [r for r in resources if r.identifier.startswith(prefix) and r.region == region]
            if matching_resources:
                vpc_children[type_key] = {
                    "name": f"{display_name} ({region})",
                    "type": type_key,
                    "children": {}
                }
        
        # Get ECS-related resources for this region
        ecs_clusters = [r for r in resources if r.identifier.startswith("aws_ecs_cluster.") and r.region == region]
        ecs_services = [r for r in resources if r.identifier.startswith("aws_ecs_service.") and r.region == region]
        task_definitions = [r for r in resources if r.identifier.startswith("aws_ecs_task_definition.") and r.region == region]
        subnets = [r for r in resources if r.identifier.startswith("aws_subnet.") and r.region == region]
        
        # Handle ECS resources for this region
        if ecs_clusters:
            cluster_parent = vpc_children
            
            # If subnet exists, place ECS under subnet
            if subnets:
                vpc_children["aws-subnet"] = {
                    "name": f"Subnet ({region})",
                    "type": "Subnet",
                    "children": {}
                }
                cluster_parent = vpc_children["aws-subnet"]["children"]
            
            # Add ECS cluster
            cluster_parent["aws-ecs-cluster"] = {
                "name": f"ECS Cluster ({region})",
                "type": "aws-ecs-cluster",
                "children": {}
            }
            cluster_children = cluster_parent["aws-ecs-cluster"]["children"]
            
            # Add ECS service under cluster
            if ecs_services:
                cluster_children["aws-ecs-service"] = {
                    "name": f"ECS Service ({region})",
                    "type": "aws-ecs-service",
                    "children": {}
                }
                service_children = cluster_children["aws-ecs-service"]["children"]
                
                # Add ECS task definition under service
                if task_definitions:
                    service_children["aws-ecs-task-definition"] = {
                        "name": f"ECS Task Definition ({region})",
                        "type": "aws-ecs-task-definition",
                        "children": {}
                    }
            
        # Add subnet if it exists and wasn't added with ECS
        elif subnets:
            vpc_children["aws-subnet"] = {
                "name": f"Subnet ({region})",
                "type": "Subnet",
                "children": {}
            }
    
    return hierarchy


def format_hierarchy(hierarchy: Dict[str, Any], indent: int = 2) -> str:
    """
    Format the hierarchy dictionary as a properly indented JSON string.
    
    Args:
        hierarchy (Dict[str, Any]): The hierarchy dictionary to format
        indent (int): Number of spaces for indentation
        
    Returns:
        str: Formatted JSON string
    """
    return json.dumps(hierarchy, indent=indent)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python terraform_hierarchy.py <terraform_content_file>")
        sys.exit(1)
        
    # Read content from file
    with open(sys.argv[1], 'r') as f:
        content = f.read()
    
    # Create and print hierarchy
    hierarchy = create_aws_hierarchy(content)
    print(format_hierarchy(hierarchy))
