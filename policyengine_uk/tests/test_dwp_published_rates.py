"""DWP rate parameters against DWP's "Benefit and pension rates" publications.

The fixture fixtures/dwp_benefit_and_pension_rates.yaml lists, for each
parameter with a published counterpart, the rate for each fiscal year as
published by DWP (and HMRC for tax credits). Each year appears in two
documents, that year's and the next year's, and the fixture holds the value
both agree on. Values are in the parameter's own unit and period.

Invariants:

1. Differential: the value PolicyEngine uses for each fiscal year (the
   parameter at 30 April, after uprating) equals the published rate.
2. No projection overrides a published rate: no fixture parameter uprates from
   a fixed `start_instant`, which would replace later published values with
   projections.
3. Projections continue from the last published rate: for a series published
   through 2026-27, an uprated parameter in 2027-28 equals the 2026-27 rate
   times the change in its uprating index, so there is no jump when
   projections begin.
4. The carer premium for two carers is twice the premium for one, in every
   year, because it is paid for each person who satisfies the condition.
5. Housing Benefit non-dependant deductions: each year's bands and deductions
   are the published ones; a band includes its lower edge ("not less than",
   HB Regs 2006 reg 74(2)); nobody with income pays less than the lowest
   deduction; and the deduction never falls as income rises.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml

from policyengine_uk.system import system

FIXTURE = yaml.safe_load(
    (
        Path(__file__).parent / "fixtures" / "dwp_benefit_and_pension_rates.yaml"
    ).read_text()
)
PARAMETERS = FIXTURE["parameters"]


def node(name: str):
    parameter = system.parameters
    for part in name.split("."):
        parameter = getattr(parameter, part)
    return parameter


CASES = [
    (name, int(year), value)
    for name, entry in PARAMETERS.items()
    for year, value in entry["values"].items()
]


@pytest.mark.parametrize(
    "name,year,published", CASES, ids=[f"{n}-{y}" for n, y, _ in CASES]
)
def test_parameter_equals_published_rate(name, year, published):
    """Invariant 1."""
    assert node(name)(f"{year}-04-30") == pytest.approx(published, abs=0.005)


@pytest.mark.parametrize("name", sorted(PARAMETERS))
def test_no_start_instant_overrides_published_rates(name):
    """Invariant 2."""
    uprating = node(name).metadata.get("uprating")
    assert not (isinstance(uprating, dict) and "start_instant" in uprating)


@pytest.mark.parametrize("name", sorted(PARAMETERS))
def test_projection_continues_from_last_published_rate(name):
    """Invariant 3."""
    parameter = node(name)
    uprating = parameter.metadata.get("uprating")
    if not uprating:
        pytest.skip("not uprated")
    last = max(int(y) for y in PARAMETERS[name]["values"])
    if last < 2026:
        pytest.skip("series ends before 2026-27")
    index = node(uprating if isinstance(uprating, str) else uprating["parameter"])
    ratio = index(f"{last + 1}-01-01") / index(f"{last}-01-01")
    expected = PARAMETERS[name]["values"][last] * ratio
    assert parameter(f"{last + 1}-04-30") == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize("year", range(2015, 2041))
def test_two_carer_premium_is_twice_the_one_carer_premium(year):
    """Invariant 4."""
    premium = system.parameters.gov.dwp.carer_premium
    at = f"{year}-04-30"
    assert premium.couple(at) == pytest.approx(2 * premium.single(at), abs=1e-6)


NON_DEP = FIXTURE["housing_benefit_non_dependant_deductions"]
NON_DEP_SCALE = system.parameters.gov.dwp.housing_benefit.non_dep_deduction.amount


@pytest.mark.parametrize("year", sorted(NON_DEP))
def test_non_dependant_deductions_match_the_published_table(year):
    """Invariant 5: bands, deductions and the inclusive lower edges."""
    at = f"{year}-04-30"
    edges = NON_DEP[year]["lower_edges"]
    deductions = NON_DEP[year]["deductions"]
    brackets = NON_DEP_SCALE.brackets
    assert [b.threshold(at) for b in brackets] == pytest.approx([0] + edges)
    assert [b.amount(at) for b in brackets] == pytest.approx(deductions)
    scale = system.parameters(at).gov.dwp.housing_benefit.non_dep_deduction.amount
    incomes = np.array([0.0] + [e - 0.01 for e in edges] + edges)
    expected = [deductions[0]] + deductions[:-1] + deductions[1:]
    assert scale.calc(incomes) == pytest.approx(expected)
    grid = np.linspace(0, edges[-1] * 1.5, 2_001)
    values = scale.calc(grid)
    assert np.all(np.diff(values) >= 0) and values.min() == deductions[0]
