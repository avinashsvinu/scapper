.PHONY: lint test fix validate clean

# Default target
validate: lint test

# Lint all Python files with pylint
lint:
	pylint $$(git ls-files '*.py')

# Placeholder for running tests
# Replace with your test runner if you add tests
# Example: pytest

test:
	@echo "No tests defined yet. Add your test runner here."

# Auto-fix Python files with autopep8 (if installed)
fix:
	autopep8 --in-place --aggressive --aggressive $$(git ls-files '*.py') || echo "autopep8 not installed. Skipping fix."

# Clean up Python cache files
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 