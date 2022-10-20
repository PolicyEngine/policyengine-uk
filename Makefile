all: install
	pip install wheel
	python setup.py sdist bdist_wheel

install:
	pip install -e .

microdata:
	python policyengine_uk/initial_setup.py

test-setup:
	python policyengine_uk/tools/testing_setup.py

format:
	autopep8 -r . --in-place
	black . -l 79

test:
	openfisca-uk test policyengine_uk/tests/policy/baseline
	openfisca-uk test policyengine_uk/tests/policy/reforms/parametric
	pytest policyengine_uk/tests/code_health -vv
	pytest policyengine_uk/tests/microsimulation/ -vv

serve:
	openfisca serve --country-package policyengine_uk

summary-stats:
	python docs/summary/generate_descriptions.py
	python docs/summary/generate_summary.py

documentation: summary-stats
	jb clean docs/book
	jb build docs/book -W

changelog:
	build-changelog changelog.yaml --output changelog.yaml --update-last-date --start-from 0.1.0 --append-file changelog_entry.yaml
	build-changelog changelog.yaml --org PolicyEngine --repo openfisca-uk --output CHANGELOG.md --template .github/changelog_template.md
	bump-version changelog.yaml setup.py
	rm changelog_entry.yaml || true
	touch changelog_entry.yaml

calibrate:
	python policyengine_uk/calibration/calibrate.py

calibration-dashboard:
	streamlit run policyengine_uk/data/datasets/frs/enhanced/stages/calibration/monitor.py
