import os
from pathlib import Path
from typing import List


def get_terraform_contents(folder_path: str) -> str:
    """
    Recursively searches for .tf and .tfvars files in the given folder and returns
    their concatenated contents.
    
    Args:
        folder_path (str): Path to the folder to search in
        
    Returns:
        str: Concatenated contents of all .tf and .tfvars files
    """
    def find_terraform_files(directory: str) -> List[str]:
        """
        Helper function to recursively find all .tf and .tfvars files
        
        Args:
            directory (str): Directory to search in
            
        Returns:
            List[str]: List of paths to terraform files
        """
        terraform_files = []
        
        # Convert to Path object for easier handling
        path = Path(directory)
        
        # Recursively search for .tf and .tfvars files
        for item in path.rglob("*"):
            if item.is_file() and item.suffix in [".tf", ".tfvars"]:
                terraform_files.append(str(item))
                
        return terraform_files
    
    # Get all terraform files
    terraform_files = find_terraform_files(folder_path)
    
    # Read and concatenate contents
    combined_contents = []
    for file_path in sorted(terraform_files):  # Sort for consistent ordering
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Add file path as a comment for better traceability
                combined_contents.append(f"\n# File: {file_path}\n")
                combined_contents.append(f.read())
        except Exception as e:
            combined_contents.append(f"\n# Error reading {file_path}: {str(e)}\n")
    
    # Join all contents with newlines
    return "\n".join(combined_contents)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python terraform_reader.py <folder_path>")
        sys.exit(1)
        
    folder_path = sys.argv[1]
    result = get_terraform_contents(folder_path)
    print(result)
