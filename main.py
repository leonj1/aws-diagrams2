#!/usr/bin/env python3
import json
import sys
import argparse
from terraform_reader import get_terraform_contents
from terraform_hierarchy import create_aws_hierarchy
from diagram_generator import create_diagram


def main():
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
            create_diagram(hierarchy, args.output)
        except Exception as e:
            print(f"Error generating diagram: {str(e)}", file=sys.stderr)
            sys.exit(1)
        
        print("Done! 🎉")
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
