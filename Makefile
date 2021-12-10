all: install
	pip install wheel
	python setup.py sdist bdist_wheel

install:
	pip install -e .

microdata:
	python openfisca_uk/initial_setup.py

test-setup:
	python openfisca_uk/tools/testing_setup.py

format:
	autopep8 -r .
	black . -l 79

test:
	openfisca test -c openfisca_uk openfisca_uk/tests/policy/baseline
	openfisca test -c openfisca_uk openfisca_uk/tests/policy/reforms/with_postcode_features -r openfisca_uk.config.postcode_lookup.with_postcode_features
	pytest openfisca_uk/tests/code_health -vv
	pytest openfisca_uk/tests/microsimulation/ -vv

serve:
	openfisca serve --country-package openfisca_uk

documentation:
	python docs/summary/generate_descriptions.py
	jb clean docs/book
	jb build docs/book
