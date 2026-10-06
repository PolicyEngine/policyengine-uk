"""Every program in programs.yaml must name model objects that exist.

programs.yaml is the program registry served through /uk/metadata as
modelled_policies. Its ``variable`` and ``parameter_prefix`` fields point
consumers at the model's variables and parameter tree, so a name that does not
exist is a dead reference downstream. The registry named the variables ``JSA``,
``ESA`` and ``DLA`` (the variables are ``jsa``, ``esa`` and ``dla``) and
``winter_fuel_payment`` (the variable is ``winter_fuel_allowance``).
"""

from collections import Counter
from pathlib import Path

import pytest
import yaml

from policyengine_uk import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()
PROGRAMS = yaml.safe_load(Path(CountryTaxBenefitSystem.modelled_policies).read_text())[
    "programs"
]

# Fields every entry carries (docs/engineering/skills/model-structure.md).
REQUIRED_FIELDS = (
    "id",
    "name",
    "full_name",
    "category",
    "agency",
    "status",
    "coverage",
    "verified_start_year",
)


def programs_with(field):
    return pytest.mark.parametrize(
        "program",
        [program for program in PROGRAMS if program.get(field) is not None],
        ids=lambda program: program["id"],
    )


@programs_with("variable")
def test_program_variable_exists(program):
    assert program["variable"] in SYSTEM.variables, (
        f"programs.yaml entry {program['id']!r} names variable "
        f"{program['variable']!r}, which is not in the tax-benefit system"
    )


@programs_with("parameter_prefix")
def test_program_parameter_prefix_resolves(program):
    try:
        SYSTEM.parameters.get_child(program["parameter_prefix"])
    except ValueError as error:
        pytest.fail(
            f"programs.yaml entry {program['id']!r} names parameter_prefix "
            f"{program['parameter_prefix']!r}, which does not resolve: {error}"
        )


def test_program_ids_are_unique():
    counts = Counter(program["id"] for program in PROGRAMS)
    repeated = sorted(id for id, count in counts.items() if count > 1)
    assert not repeated, f"programs.yaml repeats ids {repeated}"


@pytest.mark.parametrize(
    "program", PROGRAMS, ids=lambda program: str(program.get("id"))
)
def test_program_has_required_fields(program):
    missing = [field for field in REQUIRED_FIELDS if program.get(field) is None]
    assert not missing, f"programs.yaml entry {program.get('id')!r} lacks {missing}"


@programs_with("verified_end_year")
def test_program_verified_years_are_ordered(program):
    assert program["verified_start_year"] <= program["verified_end_year"]
