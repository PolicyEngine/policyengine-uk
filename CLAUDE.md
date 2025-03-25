# Development Guidelines for PolicyEngine UK

## Build Commands
- Install: `make install` or `pip install -e ".[dev]" --config-settings editable_mode=compat`
- Format code: `make format` or `black . -l 79`
- Run all tests: `make test`
- Run single test: `pytest policyengine_uk/tests/path/to/test_file.py::test_function -v`
- Generate documentation: `make documentation`
- Update changelog: `make changelog`

## Code Standards
- **Formatting**: Use Black with 79-character line length
- **Imports**: Group imports by stdlib, third-party, local with each group alphabetized
- **Naming**: Use snake_case for variables/functions, CamelCase for classes
- **Type Hints**: Use Python type hints where possible
- **Error Handling**: Handle exceptions gracefully with appropriate error messages
- **Testing**: Write tests for all new functionality
- **Documentation**: Document all public functions with docstrings
- **Versioning**: Follow SemVer (increment patch for fixes, minor for features, major for breaking changes)
- **Pull Requests**: Add entries to changelog_entry.yaml, run `make changelog`, and commit results

## Repository Structure
- **parameters/**: YAML files that define tax rates, thresholds, and other policy parameters
  - Organized by government department (e.g., gov/hmrc/, gov/dwp/, gov/dfe/)
  - Parameter labels should be lowercase and concise
  - Each parameter file should include relevant legislative references
- **variables/**: Python files that define the formulas for calculating tax and benefit amounts
  - Organized to match the same structure as parameters/
  - Comments should include relevant regulatory citations and calculation logic
- **tests/**: Test cases for validating correct implementation of policies
- For government departments, use the correct department for the policy (e.g., education policies under DfE, not DWP)