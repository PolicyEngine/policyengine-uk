"""Keep the public program registry linked to real model objects."""

import pytest
import yaml
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
