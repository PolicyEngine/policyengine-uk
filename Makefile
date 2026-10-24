.PHONY: docs test test-yaml test-python test-ci

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

# Every Python test, serially. To spread them over four cores add
# PYTEST_ARGS="-n 4 --dist worksteal" (pytest-xdist); to run what one CI
# shard runs, add "--shard K/5" (policyengine_uk/tests/conftest.py). CI runs
# these tests through .github/workflows/test-suite.yaml, in the locked
# environment (uv sync --frozen --extra dev), and also checks each test's
# outcome against .github/test_outcome_allowlist.toml.
test-python:
	pytest policyengine_uk/tests/ --cov=policyengine_uk --cov-report=xml --maxfail=0 -v $(PYTEST_ARGS)

# The same checks CI makes: the locked environment, xfail markers strict, and
# every skip or expected failure on .github/test_outcome_allowlist.toml. For a
# full run only; with --shard, CI compares all the shards' outcome logs.
test-ci:
	uv sync --frozen --extra dev
	uv run --frozen --no-sync policyengine-core test policyengine_uk/tests/policy -c policyengine_uk
	out=$$(mktemp -d) && \
	uv run --frozen --no-sync pytest policyengine_uk/tests --collect-only -q -p no:cacheprovider > $$out/collected.txt && \
	{ PYTHONPATH=.github uv run --frozen --no-sync pytest policyengine_uk/tests -p no:cacheprovider \
		-p pytest_outcome_log --outcome-log=$$out/outcomes.jsonl -o xfail_strict=true --maxfail=0 $(PYTEST_ARGS); \
	  tests=$$?; \
	  python3 .github/check_test_shards.py --collected $$out/collected.txt --outcomes $$out/outcomes.jsonl \
		--allowlist .github/test_outcome_allowlist.toml \
		--data $$(if [ -n "$$HUGGING_FACE_TOKEN$$POLICYENGINE_UK_DEFAULT_DATASET" ]; then echo present; else echo absent; fi); \
	  check=$$?; \
	  if [ $$check -ne 0 ]; then exit $$check; fi; \
	  if [ $$tests -ne 0 ] && [ $$tests -ne 1 ]; then echo "pytest exited $$tests"; exit $$tests; fi; }

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