from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceNode:
    """
    Represents a node in an AWS resource hierarchy.
    
    Attributes:
        name (str): The name of the resource
        identifier (str): Unique identifier for the resource
        is_parent (bool): Indicates if this resource can contain other resources
    """
    name: str
    identifier: str
    is_parent: bool
    region: str = "us-east-1"  # Default region if not specified
    
    def __post_init__(self):
        """Validate the node attributes after initialization."""
        if not self.name:
            raise ValueError("Resource name cannot be empty")
        if not self.identifier:
            raise ValueError("Resource identifier cannot be empty")
    
    def __str__(self) -> str:
        """Return a human-readable string representation of the resource node."""
        parent_status = "parent" if self.is_parent else "child"
        return f"ResourceNode(name='{self.name}', identifier='{self.identifier}', type={parent_status})"
    
    def __repr__(self) -> str:
        """Return a detailed string representation of the resource node."""
        return f"ResourceNode(name='{self.name}', identifier='{self.identifier}', is_parent={self.is_parent})"
    
    @property
    def display_name(self) -> str:
        """
        Get a formatted display name for the resource.
        
        Returns:
            str: A formatted string combining name and identifier
        """
        return f"{self.name} ({self.identifier})"
    
    def to_dict(self) -> dict:
        """
        Convert the resource node to a dictionary representation.
        
        Returns:
            dict: Dictionary containing the node's properties
        """
        return {
            "name": self.name,
            "identifier": self.identifier,
            "is_parent": self.is_parent,
            "region": self.region
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResourceNode':
        """
        Create a ResourceNode instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing node properties
            
        Returns:
            ResourceNode: New instance created from the dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {'name', 'identifier', 'is_parent'}
        optional_fields = {'region'}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        return cls(
            name=data['name'],
            identifier=data['identifier'],
            is_parent=data['is_parent'],
            region=data.get('region', 'us-east-1')  # Use default if not provided
        )
