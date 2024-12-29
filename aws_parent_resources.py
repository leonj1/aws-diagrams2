"""
This module defines AWS resources that are allowed to be parent resources in AWS architecture.
These resources can contain or logically group other AWS resources.
"""

# Set of AWS resource types that can be parent resources
AWS_PARENT_RESOURCES = {
    'aws_vpc',           # Virtual Private Cloud - network isolation
    'aws_subnet',        # Subnet within VPC - network segment
    'aws_ecs_cluster',   # ECS Cluster - container orchestration
    'aws_ecs_service',   # ECS Service - running container tasks
}


def is_parent_resource(resource_type: str) -> bool:
    """
    Check if a given AWS resource type is allowed to be a parent resource.

    Args:
        resource_type (str): The AWS resource type to check (e.g., 'aws_vpc')

    Returns:
        bool: True if the resource type can be a parent, False otherwise
    """
    return resource_type in AWS_PARENT_RESOURCES


def get_all_parent_resources() -> set[str]:
    """
    Get all AWS resource types that can be parent resources.

    Returns:
        set[str]: Set of all allowed parent resource types
    """
    return AWS_PARENT_RESOURCES.copy()
