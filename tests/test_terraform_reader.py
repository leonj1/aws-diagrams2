import unittest
import os
import tempfile
from pathlib import Path
from terraform_reader import get_terraform_contents

class TestTerraformReader(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Clean up temporary files
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def create_test_file(self, path: str, content: str):
        """Helper to create a test file with content"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_get_terraform_contents_single_file(self):
        # Test reading a single terraform file
        test_content = 'resource "aws_instance" "example" {}'
        test_file = os.path.join(self.test_dir, "main.tf")
        self.create_test_file(test_file, test_content)

        result = get_terraform_contents(self.test_dir)
        self.assertIn(test_content, result)
        self.assertIn(f"# File: {test_file}", result)

    def test_get_terraform_contents_multiple_files(self):
        # Test reading multiple terraform files
        files = {
            "main.tf": 'resource "aws_instance" "main" {}',
            "variables.tfvars": 'instance_type = "t2.micro"',
            "nested/network.tf": 'resource "aws_vpc" "main" {}'
        }
        
        for file_path, content in files.items():
            full_path = os.path.join(self.test_dir, file_path)
            self.create_test_file(full_path, content)

        result = get_terraform_contents(self.test_dir)
        
        # Verify all contents are present
        for file_path, content in files.items():
            full_path = os.path.join(self.test_dir, file_path)
            self.assertIn(content, result)
            self.assertIn(f"# File: {full_path}", result)

    def test_non_existent_folder(self):
        # Test handling of non-existent folder
        non_existent_path = os.path.join(self.test_dir, "does_not_exist")
        with self.assertRaises(FileNotFoundError):
            get_terraform_contents(non_existent_path)

    def test_empty_folder(self):
        # Test handling of folder with no terraform files
        with self.assertRaises(ValueError) as context:
            get_terraform_contents(self.test_dir)
        self.assertIn("No terraform files", str(context.exception))

    def test_file_read_error(self):
        # Test handling of file read errors
        test_file = os.path.join(self.test_dir, "main.tf")
        self.create_test_file(test_file, "test content")
        
        # Remove read permissions
        os.chmod(test_file, 0o000)
        
        try:
            result = get_terraform_contents(self.test_dir)
            self.assertIn(f"# Error reading {test_file}", result)
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o666)

    def test_mixed_file_types(self):
        # Test that only .tf and .tfvars files are processed
        files = {
            "main.tf": 'resource "aws_instance" "main" {}',
            "variables.tfvars": 'instance_type = "t2.micro"',
            "readme.md": '# This should be ignored',
            "script.sh": 'echo "This should be ignored"'
        }
        
        for file_path, content in files.items():
            full_path = os.path.join(self.test_dir, file_path)
            self.create_test_file(full_path, content)

        result = get_terraform_contents(self.test_dir)
        
        # Verify terraform files are included
        self.assertIn('resource "aws_instance"', result)
        self.assertIn('instance_type = "t2.micro"', result)
        
        # Verify non-terraform files are excluded
        self.assertNotIn('# This should be ignored', result)
        self.assertNotIn('echo "This should be ignored"', result)

if __name__ == '__main__':
    unittest.main()
