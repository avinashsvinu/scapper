.PHONY: lint test fix validate clean coverage

# Default target
validate: lint test

# Lint all Python files with pylint
lint:
	pylint $$(git ls-files '*.py')

# Run tests with pytest using python3.9
# Ignores test_login_session.py by default
# Outputs coverage and missing lines

test:
	python3.9 -m pytest --maxfail=1 --disable-warnings --ignore=test_login_session.py --cov=. --cov-report=term-missing -v | tee test-results.txt

# Auto-fix Python files with autopep8 (if installed)
fix:
	autopep8 --in-place --aggressive --aggressive $$(git ls-files '*.py') || echo "autopep8 not installed. Skipping fix."

# Clean up Python cache files
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

coverage:
	python3.9 -m pytest --cov=. --cov-report=term-missing tests/ 