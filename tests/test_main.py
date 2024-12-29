import pytest
import sys
import os
import tempfile
from main import main


def test_main_with_empty_folder(capsys):
    """Test main function with an empty folder."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run with empty folder
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ["main.py", temp_dir]
            main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


def test_main_with_terraform_files(capsys):
    """Test main function with valid terraform files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test terraform file
        with open(os.path.join(temp_dir, "main.tf"), "w") as f:
            f.write('''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
''')
        
        # Run with test folder
        sys.argv = ["main.py", temp_dir]
        main()
        
        captured = capsys.readouterr()
        assert "Done!" in captured.out
        assert os.path.exists("aws_architecture.png")


def test_main_with_custom_output(capsys):
    """Test main function with custom output filename."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test terraform file
        with open(os.path.join(temp_dir, "main.tf"), "w") as f:
            f.write('''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
''')
        
        # Run with custom output filename
        output_name = "test_diagram"
        sys.argv = ["main.py", temp_dir, "-o", output_name]
        main()
        
        captured = capsys.readouterr()
        assert "Done!" in captured.out
        assert os.path.exists(f"{output_name}.png")


def test_main_with_invalid_folder(capsys):
    """Test main function with non-existent folder."""
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["main.py", "/nonexistent/folder"]
        main()
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up generated diagram files after each test."""
    yield
    # Remove any generated diagram files
    for file in os.listdir():
        if file.endswith(".png"):
            os.remove(file)
