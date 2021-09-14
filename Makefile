all: microdata

install:
	pip install -e .

microdata:
	python openfisca_uk/initial_setup.py

format:
	black . -l 79

test: 
	pytest tests/setup
	openfisca test -c openfisca_uk tests/baseline
	openfisca test -c openfisca_uk tests/reforms/with_postcode_features -r openfisca_uk.config.postcode_lookup.with_postcode_features
	pytest tests/code
	pytest tests/with_microdata
	black . -l 79 --check

serve:
	openfisca serve --country-package openfisca_uk

stats:
	python docs/summary/generate_descriptions.py