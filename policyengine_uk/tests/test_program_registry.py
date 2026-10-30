"""Keep the public program registry linked to real model objects."""

import pytest
import yaml
from hypothesis import given, settings, strategies as st
from policyengine_core.parameters import ParameterNode

from policyengine_uk import CountryTaxBenefitSystem

PROGRAMS = yaml.safe_load(CountryTaxBenefitSystem.modelled_policies.read_text())[
    "programs"
]


@pytest.fixture(scope="module")
def tax_benefit_system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "program", [p for p in PROGRAMS if "variable" in p], ids=lambda p: p["id"]
)
def test_program_variables_exist(program, tax_benefit_system):
    assert program["variable"] in tax_benefit_system.variables, (
        f"{program['id']} references unknown variable {program['variable']!r}"
    )


@pytest.mark.parametrize(
    "program", [p for p in PROGRAMS if "parameter_prefix" in p], ids=lambda p: p["id"]
)
def test_program_parameter_prefixes_exist(program, tax_benefit_system):
    prefix = program["parameter_prefix"]
    assert isinstance(tax_benefit_system.parameters.get_child(prefix), ParameterNode), (
        f"{program['id']} parameter prefix {prefix!r} does not name a parameter node"
    )


def test_maternity_allowance_does_not_advertise_unrelated_parameters():
    """Reported Maternity Allowance has no policy parameter subtree (#2116)."""
    program = next(p for p in PROGRAMS if p["id"] == "maternity_allowance")
    assert "parameter_prefix" not in program


def test_benefit_cap_does_not_advertise_unrelated_parameters(tax_benefit_system):
    """The advertised Benefit Cap subtree excludes other DWP programs (#2116)."""
    program = next(p for p in PROGRAMS if p["id"] == "benefit_cap")
    advertised = tax_benefit_system.parameters.get_child(program["parameter_prefix"])
    benefit_cap = tax_benefit_system.parameters.gov.dwp.benefit_cap

    assert "universal_credit" not in advertised.children
    assert "JSA" not in advertised.children
    assert advertised.get_child("single.in_london") is benefit_cap.single.in_london
    assert (
        advertised.get_child("non_single.outside_london")
        is benefit_cap.non_single.outside_london
    )


@pytest.mark.parametrize(
    "program_id, field, expected",
    [
        ("scottish_income_tax", "agency", "HMRC"),
        ("tax_credits", "agency", "HMRC"),
        ("energy_price_guarantee", "agency", "DESNZ"),
        ("council_tax", "coverage", "Great Britain"),
        ("council_tax_reduction", "coverage", "Great Britain"),
        (
            "winter_fuel_payment",
            "coverage",
            "England, Wales and Northern Ireland",
        ),
    ],
    ids=lambda value: value,
)
def test_program_agency_and_coverage(program_id, field, expected):
    """The registry identifies the administering body and nations (#2696)."""
    programs = [p for p in PROGRAMS if p["id"] == program_id]
    assert len(programs) == 1
    assert programs[0][field] == expected


@settings(max_examples=len(PROGRAMS), database=None, derandomize=True)
@given(program_id=st.sampled_from(tuple(p["id"] for p in PROGRAMS)))
def test_program_metadata_survives_loading(tax_benefit_system, program_id):
    """Core exposes every program's agency and coverage strings unchanged."""
    registry_program = next(p for p in PROGRAMS if p["id"] == program_id)
    loaded_programs = [
        p
        for p in tax_benefit_system.modelled_policies["programs"]
        if p["id"] == program_id
    ]
    assert len(loaded_programs) == 1
    for field in ("agency", "coverage"):
        value = loaded_programs[0][field]
        assert isinstance(value, str)
        assert value
        assert value == registry_program[field]
