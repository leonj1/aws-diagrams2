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
        
        # Add route table
        route_tables = [r for r in resources if r.identifier.startswith("aws_route_table.")]
        if route_tables:
            vpc_children["aws-route-table"] = {
                "name": "Route Table",
                "type": "aws-route-table",
                "children": {}
            }
        
        # Add route table association
        rt_associations = [r for r in resources if r.identifier.startswith("aws_route_table_association.")]
        if rt_associations:
            vpc_children["aws-route-table-association"] = {
                "name": "Route Table Association",
                "type": "aws-route-table-association",
                "children": {}
            }
        
        # Add IAM role
        iam_roles = [r for r in resources if r.identifier.startswith("aws_iam_role.")]
        if iam_roles:
            vpc_children["aws-iam-role"] = {
                "name": "IAM Role",
                "type": "aws-iam-role",
                "children": {}
            }
        
        # Add IAM role policy attachment
        policy_attachments = [r for r in resources if r.identifier.startswith("aws_iam_role_policy_attachment.")]
        if policy_attachments:
            vpc_children["aws-iam-role-policy-attachment"] = {
                "name": "IAM Role Policy Attachment",
                "type": "aws-iam-role-policy-attachment",
                "children": {}
            }
        
        # Add security group
        security_groups = [r for r in resources if r.identifier.startswith("aws_security_group.")]
        if security_groups:
            vpc_children["aws-security-group"] = {
                "name": "AWS Security Group",
                "type": "aws-security-group",
                "children": {}
            }
        
        # Add subnet if it exists
        subnets = [r for r in resources if r.identifier.startswith("aws_subnet.")]
        if subnets:
            vpc_children["aws-subnet"] = {
                "name": "subnet",
                "type": "Subnet",
                "children": {}
            }
            subnet_children = vpc_children["aws-subnet"]["children"]
        
        # Add ECS cluster (either under subnet if it exists, or under VPC)
        ecs_clusters = [r for r in resources if r.identifier.startswith("aws_ecs_cluster.")]
        if ecs_clusters:
            ecs_cluster_node = {
                "name": "ECS Cluster",
                "type": "aws-ecs-cluster",
                "children": {}
            }
            
            # Place ECS cluster in appropriate parent
            if subnets:
                subnet_children["aws-ecs-cluster"] = ecs_cluster_node
                cluster_children = subnet_children["aws-ecs-cluster"]["children"]
            else:
                vpc_children["aws-ecs-cluster"] = ecs_cluster_node
                cluster_children = vpc_children["aws-ecs-cluster"]["children"]
            
            # Add ECS service if it exists
            ecs_services = [r for r in resources if r.identifier.startswith("aws_ecs_service.")]
            if ecs_services:
                cluster_children["aws-ecs-service"] = {
                    "name": "ECS Service",
                    "type": "aws-ecs-service",
                    "children": {}
                }
                service_children = cluster_children["aws-ecs-service"]["children"]
                
                # Add ECS task definition if it exists
                task_definitions = [r for r in resources if r.identifier.startswith("aws_ecs_task_definition.")]
                if task_definitions:
                    service_children["aws-ecs-task-definition"] = {
                        "name": "ECS Task Definition",
                        "type": "aws-ecs-task-definition",
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
