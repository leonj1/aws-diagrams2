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
    # Parse terraform content into ResourceNodes
    resources = parse_terraform_files(terraform_content)
    
    # Create base hierarchy structure
    hierarchy = {
        "aws-cloud": {
            "type": "aws-cloud",
            "name": "AWS Cloud",
            "children": {
                "region": {
                    "type": "region",
                    "name": "AWS Region",
                    "children": {}
                }
            }
        }
    }
    
    # Get reference to region's children for easier access
    region_children = hierarchy["aws-cloud"]["children"]["region"]["children"]
    
    # Process VPC first as it's the top-level resource
    vpc_resources = [r for r in resources if r.identifier.startswith("aws_vpc.")]
    if vpc_resources:
        vpc = vpc_resources[0]  # Assume single VPC for this implementation
        region_children["aws-vpc"] = {
            "name": "VPC",
            "type": "VPC",
            "children": {}
        }
        vpc_children = region_children["aws-vpc"]["children"]
        
        # Add VPC-level resources
        resource_types = [
            ("aws-route-table", "Route Table", "aws_route_table."),
            ("aws-route-table-association", "Route Table Association", "aws_route_table_association."),
            ("aws-iam-role", "IAM Role", "aws_iam_role."),
            ("aws-iam-role-policy-attachment", "IAM Role Policy Attachment", "aws_iam_role_policy_attachment."),
            ("aws-security-group", "AWS Security Group", "aws_security_group."),
        ]
        
        for type_key, display_name, prefix in resource_types:
            matching_resources = [r for r in resources if r.identifier.startswith(prefix)]
            if matching_resources:
                vpc_children[type_key] = {
                    "name": display_name,
                    "type": type_key,
                    "children": {}
                }
        
        # Get ECS-related resources
        ecs_clusters = [r for r in resources if r.identifier.startswith("aws_ecs_cluster.")]
        ecs_services = [r for r in resources if r.identifier.startswith("aws_ecs_service.")]
        task_definitions = [r for r in resources if r.identifier.startswith("aws_ecs_task_definition.")]
        subnets = [r for r in resources if r.identifier.startswith("aws_subnet.")]
        
        # Handle ECS resources
        if ecs_clusters:
            cluster_parent = vpc_children
            
            # If subnet exists, place ECS under subnet
            if subnets:
                vpc_children["aws-subnet"] = {
                    "name": "subnet",
                    "type": "Subnet",
                    "children": {}
                }
                cluster_parent = vpc_children["aws-subnet"]["children"]
            
            # Add ECS cluster
            cluster_parent["aws-ecs-cluster"] = {
                "name": "ECS Cluster",
                "type": "aws-ecs-cluster",
                "children": {}
            }
            cluster_children = cluster_parent["aws-ecs-cluster"]["children"]
            
            # Add ECS service under cluster
            if ecs_services:
                cluster_children["aws-ecs-service"] = {
                    "name": "ECS Service",
                    "type": "aws-ecs-service",
                    "children": {}
                }
                service_children = cluster_children["aws-ecs-service"]["children"]
                
                # Add ECS task definition under service
                if task_definitions:
                    service_children["aws-ecs-task-definition"] = {
                        "name": "ECS Task Definition",
                        "type": "aws-ecs-task-definition",
                        "children": {}
                    }
            
        # Add subnet if it exists and wasn't added with ECS
        elif subnets:
            vpc_children["aws-subnet"] = {
                "name": "subnet",
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
