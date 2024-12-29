import re
from typing import List, Dict, Tuple
from resource_node import ResourceNode
from aws_parent_resources import is_parent_resource

def parse_terraform_providers(terraform_content: str) -> Dict[str, str]:
    """
    Parse terraform content and extract AWS provider regions.
    
    Args:
        terraform_content (str): String containing terraform configuration
        
    Returns:
        Dict[str, str]: Dictionary mapping provider aliases to regions
    """
    # Regex pattern to match AWS provider blocks
    provider_pattern = r'provider\s+"aws"\s*{([^}]+)}'
    region_pattern = r'region\s*=\s*"([^"]+)"'
    alias_pattern = r'alias\s*=\s*"([^"]+)"'
    
    providers = {}
    
    # Find all provider blocks
    for match in re.finditer(provider_pattern, terraform_content, re.DOTALL):
        block_content = match.group(1)
        
        # Extract region
        region_match = re.search(region_pattern, block_content)
        if not region_match:
            continue
        
        region = region_match.group(1)
        
        # Extract alias if present, use "default" if no alias
        alias_match = re.search(alias_pattern, block_content)
        if alias_match:
            alias = alias_match.group(1)
            providers[alias] = region
        else:
            providers["default"] = region
    
    # If no providers found, default to us-east-1
    if not providers:
        providers["default"] = "us-east-1"
        
    return providers

def parse_terraform_resources_with_providers(terraform_content: str, providers: Dict[str, str]) -> Tuple[Dict[str, str], List[ResourceNode]]:
    """
    Parse terraform content and extract resources using provided provider information.
    
    Args:
        terraform_content (str): String containing terraform configuration
        providers (Dict[str, str]): Dictionary mapping provider aliases to regions
        
    Returns:
        Tuple[Dict[str, str], List[ResourceNode]]: Tuple of (provider_regions, resources)
    """
    # Regex pattern to match resource blocks
    # Matches: resource "type" "name" { ... }
    resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s+{([^}]+)}'
    
    # Regex pattern to match provider configuration in resources
    provider_config_pattern = r'provider\s*=\s*aws\.([^\s\n\}]+)'
    
    # Find all resource blocks
    resources = []
    for match in re.finditer(resource_pattern, terraform_content, re.DOTALL):
        resource_type = match.group(1)  # aws_vpc, aws_subnet, etc.
        resource_name = match.group(2)  # local name in terraform
        block_content = match.group(3)  # resource block content
        
        # Create identifier from type and name
        identifier = f"{resource_type}.{resource_name}"
        
        # Check if this is a parent resource type
        is_parent = is_parent_resource(resource_type)
        
        # Check for provider configuration
        provider_match = re.search(provider_config_pattern, block_content)
        provider_alias = provider_match.group(1) if provider_match else "default"
        
        # Get region from provider alias
        region = providers.get(provider_alias)
        if not region:
            print(f"Warning: Provider alias '{provider_alias}' not found for resource {identifier}, providers: {providers}")
            region = "us-east-1"  # Default to us-east-1 if provider not found
        
        # Create ResourceNode with region information
        node = ResourceNode(
            name=resource_name,
            identifier=identifier,
            is_parent=is_parent,
            region=region
        )
        
        resources.append(node)
    
    return providers, resources

def parse_terraform_files(file_contents: str) -> Tuple[Dict[str, str], List[ResourceNode]]:
    """
    Parse terraform content that includes file markers and extract providers and resources.
    
    Args:
        file_contents (str): String containing terraform files content with file markers
        
    Returns:
        Tuple[Dict[str, str], List[ResourceNode]]: Tuple of (provider_regions, resources)
    """
    # Split content into individual files
    # Match both formats:
    # 1. ================\nFile: main.tf\n================\n
    # 2. # File: tmp/terraform-demo1/ecs.tf
    file_pattern = r'(?:={16,}\nFile:\s+([^\n]+)\n={16,}|#\s*File:\s+([^\n]+))\n(.*?)(?=\n(?:={16,}|\#\s*File:)|\Z)'
    
    all_resources = []
    all_providers = {}
    
    # First pass: collect all providers
    for match in re.finditer(file_pattern, file_contents, re.DOTALL):
        file_content = match.group(3)
        providers = parse_terraform_providers(file_content)
        all_providers.update(providers)
    
    print(f"Found providers: {all_providers}")
    
    # Second pass: parse resources with complete provider information
    for match in re.finditer(file_pattern, file_contents, re.DOTALL):
        file_content = match.group(3)
        _, resources = parse_terraform_resources_with_providers(file_content, all_providers)
        all_resources.extend(resources)
    
    return all_providers, all_resources

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
