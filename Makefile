# Makefile for Python project

.PHONY: test test-verbose test-coverage clean

# Default Python test command
PYTEST = python -m pytest
# Test files pattern
TEST_FILES = test_*.py

# Default target
test:
	$(PYTEST) $(TEST_FILES)

# Run tests with verbose output
test-verbose:
	$(PYTEST) -v $(TEST_FILES)

# Run tests with coverage report
test-coverage:
	$(PYTEST) --cov=. $(TEST_FILES) --cov-report term-missing

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

# Help target
help:
	@echo "Available targets:"
	@echo "  test           Run tests"
	@echo "  test-verbose   Run tests with verbose output"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  clean         Clean up Python cache files"
	@echo "  help          Show this help message"
