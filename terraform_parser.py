import re
from typing import List
from resource_node import ResourceNode
from aws_parent_resources import is_parent_resource


def parse_terraform_resources(terraform_content: str) -> List[ResourceNode]:
    """
    Parse terraform content and extract resources as ResourceNode objects.
    
    Args:
        terraform_content (str): String containing terraform configuration
        
    Returns:
        List[ResourceNode]: List of ResourceNode objects representing the resources
    """
    # Regex pattern to match resource blocks
    # Matches: resource "type" "name" { ... }
    resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s+{([^}]+)}'
    
    # Find all resource blocks
    resources = []
    for match in re.finditer(resource_pattern, terraform_content, re.DOTALL):
        resource_type = match.group(1)  # aws_vpc, aws_subnet, etc.
        resource_name = match.group(2)  # local name in terraform
        
        # Create identifier from type and name
        identifier = f"{resource_type}.{resource_name}"
        
        # Check if this is a parent resource type
        is_parent = is_parent_resource(resource_type)
        
        # Create ResourceNode
        node = ResourceNode(
            name=resource_name,
            identifier=identifier,
            is_parent=is_parent
        )
        
        resources.append(node)
    
    return resources


def parse_terraform_files(file_contents: str) -> List[ResourceNode]:
    """
    Parse terraform content that includes file markers and extract resources.
    
    Args:
        file_contents (str): String containing terraform files content with file markers
        
    Returns:
        List[ResourceNode]: List of ResourceNode objects representing the resources
    """
    # Split content into individual files
    # Match both formats:
    # 1. ================\nFile: main.tf\n================\n
    # 2. # File: tmp/terraform-demo1/ecs.tf
    file_pattern = r'(?:={16,}\nFile:\s+([^\n]+)\n={16,}|#\s*File:\s+([^\n]+))\n(.*?)(?=\n(?:={16,}|\#\s*File:)|\Z)'
    
    all_resources = []
    
    # Process each file's content
    for match in re.finditer(file_pattern, file_contents, re.DOTALL):
        # Get filename from whichever group matched
        file_name = match.group(1) if match.group(1) else match.group(2)
        file_content = match.group(3)
        
        # Parse resources from this file
        resources = parse_terraform_resources(file_content)
        all_resources.extend(resources)
    
    return all_resources


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python terraform_parser.py <terraform_content_file>")
        sys.exit(1)
        
    # Read content from file
    with open(sys.argv[1], 'r') as f:
        content = f.read()
    
    # Parse resources
    resources = parse_terraform_files(content)
    
    # Print results
    print(f"\nFound {len(resources)} resources:")
    for resource in resources:
        parent_status = "PARENT" if resource.is_parent else "child"
        print(f"- [{parent_status}] {resource.display_name}")
