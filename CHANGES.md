# Changes Log

## Multiple AWS Regions Support

Added support for multiple AWS regions in the AWS architecture diagram generator:

1. ResourceNode Changes:
- Added region attribute to ResourceNode class with default value "us-east-1"
- Updated to_dict() and from_dict() methods to handle region information

2. Terraform Parser Changes:
- Added parse_terraform_providers() function to extract region information from provider blocks
- Modified parse_terraform_resources() to include provider/region information in ResourceNodes
- Updated parse_terraform_files() to return both providers and resources
- Improved provider alias handling to support both dot notation (aws.us_east_1) and space notation (aws us_east_1)
- Added two-pass parsing to ensure all providers are collected before processing resources

3. Terraform Hierarchy Changes:
- Modified create_aws_hierarchy() to support multiple regions
- Created separate region nodes for each AWS provider
- Updated resource organization to group by region
- Added region names to node display names for clarity
- Initialized VPC structure for each region to ensure consistent hierarchy

4. Test Updates:
- Added new test_multi_region_providers() to verify multi-region support
- Updated existing tests to include provider blocks and region-specific naming
- Modified test assertions to check region-specific node structure

These changes enable the diagram generator to properly represent AWS architectures that span multiple regions, with resources correctly organized under their respective regional nodes.

## Diagram Generation Updates

1. Region Visualization Changes:
- Modified _process_node() to handle region nodes as Clusters instead of regular nodes
- Added region name extraction from node names (e.g., "AWS Region (us-east-1)" -> "Region: us-east-1")
- Updated cluster styling for regions with:
  - Larger font size (14pt) for better visibility
  - Increased margin (20px) for better spacing
  - Light gray background color for visual distinction
  - Rounded corners and consistent border styling

2. Layout Improvements:
- Increased node separation (nodesep) to 2.0 for better spacing between elements
- Increased rank separation (ranksep) to 3.0 for clearer hierarchical layout
- Adjusted padding to 3.0 for better overall diagram spacing
- Updated node dimensions:
  - Increased margin to 1.5 for better label spacing
  - Increased height to 1.5 for better proportions
  - Increased width to 2.0 for better text accommodation

3. Variable Naming:
- Added region-specific suffixes to variable names to prevent conflicts
- Updated node creation to include region information in variable names
- Maintained consistent naming convention across regions

These changes improve the visual representation of multi-region AWS architectures by properly grouping resources within their respective regional clusters and ensuring clear, well-spaced layouts.

## Bug Fixes

1. Diagram Script Generation:
- Fixed indentation issue in generated diagram script
- Improved Diagram block formatting with aligned parameters
- Corrected Python syntax for with statement block
- Ensured consistent indentation for all attributes and nested blocks

2. Provider Parsing:
- Fixed provider alias extraction to handle both aliased and default providers
- Improved region mapping to ensure resources are assigned to correct regions
- Added debug logging for provider detection
- Fixed provider configuration pattern matching
