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

## Lessons Learned from Variable Refactoring (2025-05-31)

### Issue: Refactoring Script Bug
A refactoring script was used to split multi-variable Python files into single-variable files. The script had a systematic bug: when a file contained multiple Variable classes and one had the same name as the file, that variable was dropped entirely.

### Variables Dropped During Refactoring
21 variables were dropped, including:
- Wrapper variables: `jsa_income`, `esa_income`, `jsa_contrib`, `esa_contrib`, `afcs`, `bsp`, `iidb`
- Calculated variables: `benefit_cap`, `carers_allowance`, `income_support`, `maternity_allowance`, `sda`, `tax_credits`
- Core variables: `child_benefit`, `allowances`, `marriage_allowance`, `stamp_duty_land_tax`, `vat`, `land_transaction_tax`, `attendance_allowance`, `council_tax_benefit`, `business_rates`, `tax`, `total_wealth`, `private_school_vat`, `bi_phaseout`

### Enum Recovery Errors
During recovery, enums were recreated based on assumptions rather than checking original code, leading to incorrect values:
- **TenureType**: Missing `OWNED_OUTRIGHT` and `OWNED_WITH_MORTGAGE` (consolidated into `OWNER_OCCUPIED`)
- **AccommodationType**: Wrong labels (e.g., "House - detached" vs "Detached house")
- **EducationType**: Wrong capitalization ("Lower secondary" vs "Lower Secondary")
- **FamilyType**: Shortened labels (missing ", with children" suffix)
- **EmploymentStatus**: Complete restructure (missing FT_/PT_ prefixes)
- **MinimumWageCategory**: Wrong format ("18-20" vs "18 to 20", "Over 24" vs "25 or over")
- **CouncilTaxBand**: Added incorrect "Band " prefix
- **StatePensionType**: Wrong capitalization ("Basic" vs "basic")

### Best Practices for Refactoring Recovery
1. **Always check original code** - Never rely on assumptions or context clues
2. **Use git history systematically** - `git show <commit>:path/to/file` to see original content
3. **Verify enum values exactly** - Even small differences in labels can break functionality
4. **Test incrementally** - Run tests after each fix to ensure progress
5. **Document the recovery process** - Track what was fixed for future reference

### OpenFisca-Specific Patterns
- Use `.possible_values` to access enum values, not direct imports
- Import helper functions like `find_freeze_start` when needed
- Functions like `ceil` should be `np.ceil` in OpenFisca context