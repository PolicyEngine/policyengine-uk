"""Guard the seam between the microcosm firm frame and this model.

The microcosm firm frame (PolicyEngine/microcosm PR #1706) writes the input
columns below into a dataset's firm table, and its adapter reads back the
outputs below. If a variable here is renamed, moved to another entity or
given another value type, the frame's columns would stop loading or its
adapter would read the wrong thing, so this test fails first. Change the
two sides together.
"""

import pytest

from policyengine_uk import CountryTaxBenefitSystem

# Columns the microcosm firm frame writes.
INPUTS = {
    "firm_turnover": float,
    "firm_input_costs": float,
    "firm_employees": int,
    "firm_sic_section": "Enum",
    "firm_standard_rated_supplies": float,
    "firm_exempt_supplies": float,
    "firm_vat_voluntarily_registered": bool,
    "firm_input_vat": float,
}

# Outputs the microcosm adapter reads.
OUTPUTS = {
    "firm_vat_liability_if_registered": float,
    "firm_vat_registered": bool,
}


@pytest.fixture(scope="module")
def variables():
    return CountryTaxBenefitSystem().variables


def value_type_name(value_type) -> str:
    return value_type if isinstance(value_type, str) else value_type.__name__


@pytest.mark.parametrize("name", sorted({**INPUTS, **OUTPUTS}))
def test_variable_is_a_firm_variable_of_the_expected_type(variables, name):
    expected = {**INPUTS, **OUTPUTS}[name]
    assert name in variables, f"{name} is missing from the UK system"
    variable = variables[name]
    assert variable.entity.key == "firm"
    assert value_type_name(variable.value_type) == value_type_name(expected)


@pytest.mark.parametrize("name", sorted(OUTPUTS))
def test_outputs_are_computed(variables, name):
    assert variables[name].formulas or variables[name].adds


def test_sic_section_enum_has_sections_a_to_u(variables):
    # The system loads each variable file as its own module, so compare the
    # enum by name rather than identity.
    sic_section = variables["firm_sic_section"].possible_values
    assert sic_section.__name__ == "SICSection"
    sections = [chr(code) for code in range(ord("A"), ord("U") + 1)]
    for section in sections:
        assert section in sic_section.__members__, section
    assert set(sic_section.__members__) == set(sections) | {"UNKNOWN"}
