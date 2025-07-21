# PolicyEngine UK reform impact tests

This directory contains automated tests to monitor when model changes affect the fiscal impacts of policy reforms. It helps ensure that updates to the PolicyEngine UK model don't unexpectedly change reform outcomes.

## Overview

The testing framework consists of three main components:

1. **reforms_config.yaml** - Configuration file containing reform definitions and their expected impacts
2. **test_reform_impacts.py** - Pytest test suite that verifies reforms produce expected impacts
3. **update_reform_impacts.py** - Script to update expected impacts when model changes are intentional

## Quick start

### Running tests

To check if current model produces expected reform impacts:

```bash
pytest test_reform_impacts.py
```

To run with more detail:

```bash
pytest test_reform_impacts.py -v
```

### Updating expected impacts

When model changes are intentional and you need to update the baseline expectations:

```bash
# Preview changes without updating
python update_reform_impacts.py --dry-run

# Update the configuration file
python update_reform_impacts.py

# Update with detailed output
python update_reform_impacts.py --verbose
```

## Configuration file structure

The `reforms_config.yaml` file defines each reform with:

```yaml
reforms:
  - name: "Description of the reform"
    expected_impact: 10.5  # Fiscal impact in billions
    parameters:
      "gov.some.parameter": 0.25
      "gov.another.parameter": 1000
```

## Workflow

### Regular testing

1. Run `pytest policyengine_uk/tests/microsimulation/test_reform_impacts.py` as part of your CI/CD pipeline
2. Tests will fail if any reform impact differs by more than £0.1 billion from expected
3. This catches unintended consequences of model changes

### After intentional model changes

1. Run `python policyengine_uk/tests/microsimulation/update_reform_impacts.py --dry-run` to preview impact changes
2. Review the changes to ensure they're expected
3. Run `python policyengine_uk/tests/microsimulation/update_reform_impacts.py` to update the configuration
4. Commit both the model changes and updated `reforms_config.yaml`

### Adding new reforms

1. Add a new entry to `reforms_config.yaml`:
   ```yaml
   - name: "Your new reform description"
     expected_impact: 0.0  # Initial placeholder
     parameters:
       "gov.parameter.to.change": new_value
   ```

2. Run `python policyengine_uk/tests/microsimulation/update_reform_impacts.py` to calculate the actual impact
3. Run `pytest policyengine_uk/tests/microsimulation/test_reform_impacts.py` to verify the test passes

## Test tolerance

Tests allow for a tolerance of £0.1 billion in fiscal impacts. This accounts for:
- Minor numerical differences in calculations
- Small variations from microsimulation sampling

If you need to adjust this tolerance, modify the assertion in `test_reform_impacts.py`.

## Troubleshooting

### Tests failing after model update

1. Check if the changes are expected by running the update script with `--dry-run`
2. If changes are expected, update the configuration file
3. If changes are unexpected, investigate the model modifications

### Import errors

Ensure you have the required dependencies:
```bash
pip install policyengine-uk pytest pyyaml
```

### Configuration file not found

The tests expect `reforms_config.yaml` to be in the same directory as the test file. You can specify a different path:

```bash
python update_reform_impacts.py --config /path/to/reforms_config.yaml
```

## Example reforms

The configuration includes various UK tax and benefit reforms:
- Income tax rate changes (basic, higher, additional rates)
- Personal allowance adjustments
- National Insurance contribution rates
- VAT rate changes
- Universal Credit taper rate modifications
- Child benefit amount changes

Each reform's fiscal impact is measured as the change in government balance (in billions) for the year 2029.