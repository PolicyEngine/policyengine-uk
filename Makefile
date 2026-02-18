.PHONY: docs

all: install
	pip install build
	python -m build

install:
	pip install policyengine
	pip install -e ".[dev]" --config-settings editable_mode=compat
	pip install --upgrade jsonschema[format-nongpl]
	pip install huggingface_hub

format:
	black . -l 79

test:
	policyengine-core test policyengine_uk/tests/policy -c policyengine_uk
	pytest policyengine_uk/tests/ --cov=policyengine_uk --cov-report=xml --maxfail=0 -v

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
	build-changelog changelog.yaml --output changelog.yaml --update-last-date --start-from 0.1.0 --append-file changelog_entry.yaml
	build-changelog changelog.yaml --org PolicyEngine --repo openfisca-uk --output CHANGELOG.md --template .github/changelog_template.md
	bump-version changelog.yaml pyproject.toml
	rm changelog_entry.yaml || true
	touch changelog_entry.yaml
