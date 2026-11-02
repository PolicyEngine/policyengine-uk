"""The State Pension a survey reports, read back at 52 weeks a year.

basic_state_pension, new_state_pension and additional_state_pension divide
state_pension_reported by policyengine-core's 52 weeks a year and split the
weekly amount at the data year's full rate for the type the person has in the
year being calculated. A dataset must therefore annualise the State Pension at
52 weeks. At 365.25 / 7, which
policyengine-uk-data used until policyengine-uk-data#644, every full-rate
pensioner read 0.34% above the full rate and carried an add-on they do not
get, which put people whose only income is the full new State Pension on the
Pension Tax Allowance's taper, paying tax.

These cases build simulations from 2024-25 data projected forward, as survey
data is (ages held fixed, at ages whose type stays the same in every year), and
check the route from a reported weekly amount to Income Tax:

- a pensioner reporting exactly the data year's full rate has no add-on in any
  year;
- Steph, whose only income is the full new State Pension, pays no Income Tax
  in 2027-28 to 2029-30, as HM Treasury's explainer says, and the same as when
  her State Pension is given directly;
- near the full new rate, no one reporting at most the full rate pays Income
  Tax, and above it the tax never exceeds 8/15 of the add-on (20% on it plus a
  third of it off the allowance).

policyengine-core holds amounts as float32, so £11,502.40 reads back about a
thousandth of a penny above £221.20 a week (0.0012p, or 0.063p a year);
comparisons allow a penny.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.system import system

DATA_YEAR = 2024
PTA_YEARS = [2027, 2028, 2029]
WEEKS_IN_YEAR = 52
# Ages held through the projection: reached State Pension age in 2020 (new
# State Pension) and in 2005 (basic State Pension).
AGE = {"NEW": 70, "BASIC": 85}
PENNY = 0.01


def survey_simulation(weekly, pension_types) -> Microsimulation:
    """2024-25 data with one pensioner per household, reporting `weekly` a
    week of State Pension annualised at 52 weeks, and nothing else."""
    ids = np.arange(len(weekly))
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": [AGE[t] for t in pension_types],
            "gender": "FEMALE",
            "state_pension_reported": np.asarray(weekly) * WEEKS_IN_YEAR,
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": np.ones(len(ids)),
            "region": "LONDON",
            "tenure_type": "OWNED_OUTRIGHT",
            "rent": 0.0,
            "council_tax": 0.0,
        }
    )
    return Microsimulation(
        dataset=UKSingleYearDataset(
            person=person,
            benunit=pd.DataFrame({"benunit_id": ids}),
            household=household,
            fiscal_year=DATA_YEAR,
        )
    )


def calculate(sim, variable, year) -> np.ndarray:
    # A Microsimulation returns a weighted series, a Simulation an array.
    values = sim.calculate(variable, year)
    return np.asarray(getattr(values, "values", values))


def full_rates(year) -> dict:
    p = system.parameters.gov.dwp.state_pension
    return {
        "NEW": p.new_state_pension.amount(year),
        "BASIC": p.basic_state_pension.amount(year),
    }


@pytest.fixture(scope="module")
def full_rate_reporters():
    types = ["NEW", "BASIC"]
    rates = full_rates(DATA_YEAR)
    return survey_simulation([rates[t] for t in types], types), types


@pytest.mark.parametrize("year", range(DATA_YEAR, 2031))
def test_full_rate_reporters_have_no_add_on_in_any_year(full_rate_reporters, year):
    sim, types = full_rate_reporters
    rates = full_rates(year)

    assert calculate(sim, "state_pension_type", year).astype(str).tolist() == types
    assert np.all(calculate(sim, "additional_state_pension", year) < PENNY)
    assert calculate(sim, "new_state_pension", year)[0] == pytest.approx(
        WEEKS_IN_YEAR * rates["NEW"], abs=PENNY
    )
    assert calculate(sim, "basic_state_pension", year)[1] == pytest.approx(
        WEEKS_IN_YEAR * rates["BASIC"], abs=PENNY
    )


@pytest.mark.parametrize("year", PTA_YEARS)
def test_steph_pays_no_income_tax_from_survey_data_or_given_directly(
    full_rate_reporters, year
):
    """Steph's only income is the full new State Pension: £13,036.40 in
    2027-28, 52 weeks at £250.70. The Pension Tax Allowance removes all her
    tax, whether her State Pension comes from a survey's weekly amount or is
    given directly."""
    sim, _ = full_rate_reporters
    threshold = WEEKS_IN_YEAR * full_rates(year)["NEW"]
    personal_allowance = system.parameters(
        f"{year}-04-30"
    ).gov.hmrc.income_tax.allowances.personal_allowance.amount
    tax_before_allowance = 0.2 * (threshold - personal_allowance)

    direct = Simulation(
        situation={
            "people": {
                "steph": {
                    "age": {year: AGE["NEW"]},
                    "state_pension": {year: threshold},
                }
            },
            "benunits": {"benunit": {"members": ["steph"]}},
            "households": {
                "household": {"members": ["steph"], "region": {year: "LONDON"}}
            },
        }
    )

    from_survey = {
        v: calculate(sim, v, year)[0]
        for v in ("state_pension", "income_tax", "pension_tax_allowance")
    }
    given_directly = {v: calculate(direct, v, year)[0] for v in from_survey}

    assert from_survey["state_pension"] == pytest.approx(threshold, abs=PENNY)
    assert from_survey["income_tax"] == pytest.approx(0, abs=PENNY)
    # Not vacuous: without the allowance she would pay basic-rate tax.
    assert tax_before_allowance > 90
    assert from_survey["pension_tax_allowance"] == pytest.approx(
        tax_before_allowance, abs=PENNY
    )
    for v in from_survey:
        assert from_survey[v] == pytest.approx(given_directly[v], abs=PENNY), v


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    offsets=st.lists(
        st.one_of(
            st.floats(min_value=-5, max_value=5, allow_nan=False),
            st.sampled_from([0.0, -0.01, 0.01]),
        ),
        min_size=1,
        max_size=40,
    )
)
def test_near_the_full_rate_only_the_add_on_is_taxed(offsets):
    """New State Pension reporters within £5 a week of the full rate, with no
    other income, in each year of the allowance."""
    offsets = np.asarray(offsets)
    rates = full_rates(DATA_YEAR)
    sim = survey_simulation(rates["NEW"] + offsets, ["NEW"] * len(offsets))
    at_or_below = offsets <= 0
    for year in PTA_YEARS:
        add_on = calculate(sim, "additional_state_pension", year)
        tax = calculate(sim, "income_tax", year)
        assert np.all(add_on[at_or_below] < PENNY), year
        assert np.all(tax[at_or_below] < PENNY), year
        assert np.all(tax <= 8 / 15 * add_on + PENNY), year
