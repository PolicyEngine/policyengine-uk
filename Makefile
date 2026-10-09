.PHONY: docs test test-yaml test-python

# Builds the wheel from the checkout rather than from the sdist (build's
# default), so hatch_build.py can record the commit: an unpacked sdist has no
# .git. Both commands give identical artifacts apart from that record.
all: install
	pip install build
	python -m build --sdist --wheel

install:
	pip install policyengine
	pip install -e ".[dev]" --config-settings editable_mode=compat
	pip install --upgrade jsonschema[format-nongpl]
	pip install huggingface_hub

format:
	ruff format .
	ruff check .

test: test-yaml test-python

test-yaml:
	policyengine-core test policyengine_uk/tests/policy -c policyengine_uk

# CI passes PYTEST_ARGS="-n 4 --dist worksteal" (pytest-xdist) to spread the
# tests over the runner's four cores. Without it this runs serially, as before.
test-python:
	pytest policyengine_uk/tests/ --cov=policyengine_uk --cov-report=xml --maxfail=0 -v $(PYTEST_ARGS)

test-all:
	policyengine-core test policyengine_uk/tests/policy -c policyengine_uk
	pytest policyengine_uk/tests/ --cov=policyengine_uk --cov-report=xml --maxfail=0 -v

test-microsimulation:
	pytest policyengine_uk/tests/microsimulation/ -m microsimulation -v

update-tests:
	python policyengine_uk/tests/microsimulation/update_reform_impacts.py

documentation:
	cd docs/book && jupyter book clean --all -y
	cd docs/book && jupyter book build --html
	python docs/book/add_plotly_to_book.py docs/book/_build

docs: documentation

changelog:
	python .github/bump_version.py
	towncrier build --yes --version $$(python -c "import re; print(re.search(r'version = \"(.+?)\"', open('pyproject.toml').read()).group(1))")