all: install
	pip install wheel
	python setup.py sdist bdist_wheel

install:
	pip install policyengine
	pip install -e ".[dev]" --config-settings editable_mode=compat
	pip install --upgrade jsonschema[format-nongpl]
	pip install huggingface_hub

format:
	black . -l 79

test:
	policyengine-core test policyengine_uk/tests/policy -c policyengine_uk
	pytest policyengine_uk/tests/ -v

documentation:
	jb clean docs/book
	jb build docs/book
	python docs/book/add_plotly_to_book.py docs/book/_build

changelog:
	build-changelog changelog.yaml --output changelog.yaml --update-last-date --start-from 0.1.0 --append-file changelog_entry.yaml
	build-changelog changelog.yaml --org PolicyEngine --repo openfisca-uk --output CHANGELOG.md --template .github/changelog_template.md
	bump-version changelog.yaml setup.py
	rm changelog_entry.yaml || true
	touch changelog_entry.yaml

compare_psnd:
	pip uninstall policyengine-uk -y
	pip install policyengine-uk
	cd policyengine_uk/utils && python psnd.py
	mv policyengine_uk/utils/psnd.csv psnd_old.csv
	pip install -e .
	cd policyengine_uk/utils && python psnd.py
	mv policyengine_uk/utils/psnd.csv psnd_new.csv
	python .github/compare_psnd.py