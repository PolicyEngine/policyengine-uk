"""A dataset that stores a household ISA total keeps it in every year (#2740).

cash_isa, stocks_and_shares_isa and household_lifetime_isa_balance sum person
balances, but a dataset can store the household total instead. Up to
PROJECTION_END_YEAR the dataset projection grows a stored total; after it,
Simulation grows the latest stored total by the index of its parts, the index
each variable's documentation projects it with. A dataset that stores only the
person balances, or stores them for a later year than the total, gets their
sum, and so does a situation for a year it gives no total for. An input frame
is data, so a total it stores grows too.

Invariants, for any non-negative amounts:

- a stored total stays positive in every year from 2025 to 2040 when it starts
  positive, and from PROJECTION_END_YEAR grows by its declared index;
- with person balances stored instead, the total equals their sum every year;
- the two forms give the same totals and means-test capital when they hold
  the same amounts.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period
from policyengine_core.reforms import Reform
from policyengine_core.simulations.simulation import _uprating_index_value

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.data.economic_assumptions import (
    PROJECTION_END_YEAR,
    STORED_HOUSEHOLD_TOTALS,
    _uprating_index_map,
    stored_total_uprating,
)
from policyengine_uk.model_api import YEAR, Household, Variable
from policyengine_uk.scenarios import no_economic_assumptions

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

DATA_YEAR = 2025
YEARS = range(DATA_YEAR, 2041)
CAPITAL_YEARS = (DATA_YEAR, PROJECTION_END_YEAR, PROJECTION_END_YEAR + 1, YEARS[-1])
# Each total, the person balance it sums, and the variable its documentation
# says it is projected with.
TOTALS = {
    "cash_isa": ("cash_isa_balance", "savings"),
    "stocks_and_shares_isa": ("stocks_and_shares_isa_balance", "corporate_wealth"),
    "household_lifetime_isa_balance": ("lifetime_isa_balance", "lifetime_isa_balance"),
}
MEANS_TEST_CAPITAL = (
    "uc_assessable_capital",
    "housing_benefit_assessable_capital",
    "pension_credit_assessable_capital",
    "income_support_assessable_capital",
    "jsa_income_assessable_capital",
    "esa_income_assessable_capital",
    "council_tax_reduction_assessable_capital",
)
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    database=None,
)


def _dataset(households, person_columns=(), household_columns=(), year=DATA_YEAR):
    """Two adults per household, with the named columns from ``households``.

    Each household is a dict of amounts. A person column ``name`` takes
    ``name`` split between the two adults by the household's ``share``.
    """
    people = []
    for index, household in enumerate(households):
        share = household.get("share", 1.0)
        for adult, age in ((0, 30), (1, 28)):
            person = {
                "person_id": 2 * index + adult + 1,
                "person_benunit_id": index + 1,
                "person_household_id": index + 1,
                "age": age,
            }
            for name in person_columns:
                first = round(household[name] * share, 2)
                person[name] = first if adult == 0 else household[name] - first
            people.append(person)
    count = len(households)
    return UKSingleYearDataset(
        person=pd.DataFrame(people),
        benunit=pd.DataFrame({"benunit_id": range(1, count + 1)}),
        household=pd.DataFrame(
            {
                "household_id": range(1, count + 1),
                "household_weight": [1.0] * count,
                "region": ["LONDON"] * count,
                "tenure_type": ["RENT_PRIVATELY"] * count,
                "council_tax": [1_500.0] * count,
                "rent": [12_000.0] * count,
                "savings": [1_000.0] * count,
                **{
                    name: [float(household[name]) for household in households]
                    for name in household_columns
                },
            }
        ),
        fiscal_year=year,
    )


def _values(simulation, name, years=YEARS):
    return {year: simulation.calculate(name, year).astype(float) for year in years}


def _growth(simulation, name, year, base=PROJECTION_END_YEAR):
    """Growth from ``base`` to ``year`` by the index ``name`` declares."""
    index = simulation.tax_benefit_system.parameters.get_child(
        simulation.tax_benefit_system.variables[name].uprating
    )
    return _uprating_index_value(index, period(year).start) / _uprating_index_value(
        index, period(base).start
    )


def test_stored_household_totals_grow_past_the_projection_horizon():
    simulation = Simulation(
        dataset=_dataset(
            [
                {
                    "cash_isa": 3_000.0,
                    "stocks_and_shares_isa": 2_000.0,
                    "household_lifetime_isa_balance": 4_000.0,
                }
            ],
            household_columns=TOTALS,
        )
    )
    capital = _values(simulation, "uc_assessable_capital")
    savings = _values(simulation, "savings")
    for name, (_, projected_with) in TOTALS.items():
        totals = _values(simulation, name)
        for year in YEARS:
            if year <= PROJECTION_END_YEAR:
                continue
            growth = _growth(simulation, projected_with, year)
            assert growth > 1
            assert totals[year][0] == pytest.approx(
                totals[PROJECTION_END_YEAR][0] * growth, rel=1e-6
            )
    # Savings, the cash ISA and the stocks-and-shares ISA (through
    # share_like_capital) make up the capital, each grown alike.
    for year in YEARS:
        assert capital[year][0] == pytest.approx(6 * savings[year][0], rel=1e-5)


@pytest.mark.parametrize(
    "scenario", [None, no_economic_assumptions], ids=["current_law", "no_growth"]
)
def test_stored_totals_project_exactly_like_what_they_are_projected_with(scenario):
    # cash_isa is stored equal to savings, stocks_and_shares_isa to
    # corporate_wealth, and household_lifetime_isa_balance to the one
    # lifetime_isa_balance in the household: Core projects the second of each
    # pair, Simulation the first. Without economic growth both stay flat.
    household = {
        "cash_isa": 1_000.0,
        "stocks_and_shares_isa": 2_345.67,
        "corporate_wealth": 2_345.67,
        "household_lifetime_isa_balance": 4_321.09,
        "lifetime_isa_balance": 4_321.09,
    }
    simulation = Simulation(
        scenario=scenario,
        dataset=_dataset(
            [household],
            person_columns=["lifetime_isa_balance"],
            household_columns=[
                "cash_isa",
                "stocks_and_shares_isa",
                "corporate_wealth",
                "household_lifetime_isa_balance",
            ],
        ),
    )
    for name, other in (
        ("cash_isa", "savings"),
        ("stocks_and_shares_isa", "corporate_wealth"),
        ("household_lifetime_isa_balance", "lifetime_isa_balance"),
    ):
        for year in YEARS:
            total = simulation.calculate(name, year)
            assert total.sum() == simulation.calculate(other, year).sum(), (name, year)
    # So the stocks-and-shares ISA stays within corporate_wealth.
    for year in YEARS:
        share_like = simulation.calculate("share_like_capital", year)
        assert share_like[0] == simulation.calculate("corporate_wealth", year)[0]


def test_person_balances_still_sum_without_a_stored_total():
    simulation = Simulation(
        dataset=_dataset(
            [
                {
                    "cash_isa_balance": 3_000.0,
                    "stocks_and_shares_isa_balance": 2_000.0,
                    "lifetime_isa_balance": 4_000.0,
                    "share": 0.25,
                }
            ],
            person_columns=[part for part, _ in TOTALS.values()],
        )
    )
    for name, (part, _) in TOTALS.items():
        for year in YEARS:
            balances = simulation.calculate(part, year)
            assert balances[0] > 0 and balances[1] > 0
            assert simulation.calculate(name, year)[0] == pytest.approx(
                balances.sum(), rel=1e-6
            )


def test_a_situation_total_is_used_only_for_the_year_it_is_given_for():
    simulation = Simulation(
        situation={
            "people": {
                "adult": {
                    "age": {DATA_YEAR: 40},
                    "cash_isa_balance": {DATA_YEAR: 3_000},
                }
            },
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    "cash_isa": {DATA_YEAR: 7_000},
                }
            },
        }
    )
    assert simulation.calculate("cash_isa", DATA_YEAR)[0] == 7_000
    for year in (DATA_YEAR + 1, PROJECTION_END_YEAR + 1):
        balance = simulation.calculate("cash_isa_balance", year)[0]
        assert balance > 3_000
        assert simulation.calculate("cash_isa", year)[0] == balance


def test_a_total_set_on_a_branch_replaces_the_one_a_later_year_grew_from():
    # Like savings, which Core uprates, a grown total depends on which years
    # hold a total, so a total set on a branch for a year in between reaches
    # a later year the branch has already calculated.
    simulation = Simulation(
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"])
    )
    branch = simulation.get_branch("edited")
    between, later = PROJECTION_END_YEAR + 1, PROJECTION_END_YEAR + 3
    for name in ("cash_isa", "savings"):
        assert branch.calculate(name, later)[0] > 0
        branch.set_input(name, between, np.array([10_000.0]))
    growth = _growth(simulation, "savings", later, base=between)
    for name in ("cash_isa", "savings"):
        assert branch.calculate(name, later)[0] == pytest.approx(
            10_000 * growth, rel=1e-6
        )
    assert simulation.calculate("cash_isa", later)[0] == pytest.approx(
        3 * simulation.calculate("savings", later)[0], rel=1e-6
    )


def test_person_balances_stored_after_the_total_are_summed_instead():
    # A total and balances that a dataset stores for the same year: the total
    # takes precedence, and grows. Balances stored for later years than the
    # total are the newer observation, so their sum stands.
    def year(columns, person_columns=(), share=0.25, year=DATA_YEAR):
        return _dataset(
            [{**columns, "share": share}],
            person_columns=person_columns,
            household_columns=[name for name in columns if name == "cash_isa"],
            year=year,
        )

    simulation = Simulation(
        dataset=UKMultiYearDataset(
            datasets=[
                year(
                    {"cash_isa": 5_000.0, "cash_isa_balance": 400.0},
                    ["cash_isa_balance"],
                ),
                year({"cash_isa_balance": 600.0}, ["cash_isa_balance"], year=2026),
                year({"cash_isa_balance": 800.0}, ["cash_isa_balance"], year=2027),
            ]
        )
    )
    assert simulation.calculate("cash_isa", DATA_YEAR)[0] == 5_000
    assert simulation.calculate("cash_isa", 2026)[0] == pytest.approx(600)
    assert simulation.calculate("cash_isa", 2027)[0] == pytest.approx(800)
    balances = simulation.calculate("cash_isa_balance", 2028)
    assert balances.sum() > 800
    assert simulation.calculate("cash_isa", 2028)[0] == pytest.approx(
        balances.sum(), rel=1e-6
    )

    same_year = Simulation(
        dataset=UKMultiYearDataset(
            datasets=[
                year(
                    {"cash_isa": 5_000.0, "cash_isa_balance": 400.0},
                    ["cash_isa_balance"],
                ),
            ]
        )
    )
    growth = _growth(same_year, "savings", 2026, base=DATA_YEAR)
    assert same_year.calculate("cash_isa", 2026)[0] == pytest.approx(
        5_000 * growth, rel=1e-6
    )


def test_a_total_stored_in_an_input_frame_grows_like_savings():
    # An input frame is data: a total it stores grows into later years, as a
    # total in a situation does not.
    frame = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "person_benunit_id__2025": [1, 1],
            "person_household_id__2025": [1, 1],
            "age__2025": [30, 28],
            "savings__2025": [1_000.0, 1_000.0],
            "cash_isa__2025": [3_000.0, 3_000.0],
        }
    )
    simulation = Simulation(dataset=frame)
    for year in (DATA_YEAR + 1, PROJECTION_END_YEAR + 1):
        savings = simulation.calculate("savings", year)[0]
        assert savings > 1_000
        assert simulation.calculate("cash_isa", year)[0] == pytest.approx(
            3 * savings, rel=1e-6
        )


def test_a_reform_formula_for_a_total_runs_in_years_with_no_stored_total():
    # A reform that gives a total a formula replaces its sum, so Core runs the
    # formula wherever no total is stored, as for any formula variable.
    class cash_isa(Variable):
        value_type = float
        entity = Household
        label = "cash ISA holdings, twice savings"
        definition_period = YEAR

        def formula(household, period, parameters):
            return 2 * household("savings", period)

    class twice_savings(Reform):
        def apply(self):
            self.update_variable(cash_isa)

    simulation = Simulation(
        reform=twice_savings,
        dataset=_dataset([{"cash_isa": 3_000.0}], household_columns=["cash_isa"]),
    )
    for year, multiple in ((PROJECTION_END_YEAR, 3), (PROJECTION_END_YEAR + 1, 2)):
        savings = simulation.calculate("savings", year)[0]
        assert simulation.calculate("cash_isa", year)[0] == pytest.approx(
            multiple * savings, rel=1e-6
        )


def test_stored_totals_grow_by_the_index_they_are_projected_with():
    from policyengine_uk.system import system

    for name, (part, projected_with) in TOTALS.items():
        assert system.variables[name].adds == [part]
        index = system.variables[projected_with].uprating
        assert index is not None
        assert stored_total_uprating(system, name) == index


def test_every_projected_household_sum_of_uprated_inputs_is_a_stored_total():
    # A total listed for dataset projection whose parts Core uprates must keep
    # a stored value past PROJECTION_END_YEAR too.
    from policyengine_uk.system import system

    listed = {name for names in _uprating_index_map().values() for name in names}
    sums_of_uprated_inputs = {
        name
        for name in listed
        if isinstance(system.variables[name].adds, list)
        and not system.variables[name].formulas
        and all(
            system.variables[part].is_input_variable()
            and system.variables[part].uprating is not None
            for part in system.variables[name].adds
        )
    }
    assert sums_of_uprated_inputs == STORED_HOUSEHOLD_TOTALS


AMOUNTS = st.integers(min_value=0, max_value=200_000_000).map(lambda p: p / 100)
HOUSEHOLDS = st.lists(
    st.fixed_dictionaries(
        {
            "cash_isa": AMOUNTS,
            "stocks_and_shares_isa": AMOUNTS,
            "household_lifetime_isa_balance": AMOUNTS,
            "share": st.sampled_from([0.0, 0.3, 0.5, 1.0]),
        }
    ),
    min_size=1,
    max_size=6,
)


@PROPERTY_SETTINGS
@given(households=HOUSEHOLDS)
def test_stored_totals_and_person_balances_agree_in_every_year(households):
    # The totals-only dataset stores the three household totals; it also
    # stores the Lifetime ISA balances, which the means tests read from the
    # person. The balances-only dataset stores the same amounts per person.
    households = [
        {**household, **{part: household[name] for name, (part, _) in TOTALS.items()}}
        for household in households
    ]
    totals_only = Simulation(
        dataset=_dataset(
            households,
            person_columns=["lifetime_isa_balance"],
            household_columns=TOTALS,
        )
    )
    balances_only = Simulation(
        dataset=_dataset(
            households, person_columns=[part for part, _ in TOTALS.values()]
        )
    )
    members = balances_only.calculate("person_household_id", DATA_YEAR)
    for name, (part, projected_with) in TOTALS.items():
        stored = np.array([household[name] for household in households])
        totals = _values(totals_only, name)
        summed = _values(balances_only, name)
        for year in YEARS:
            assert ((totals[year] > 0) == (stored > 0)).all(), (name, year)
            balances = balances_only.calculate(part, year)
            sums = np.bincount(members - 1, weights=balances, minlength=len(stored))
            assert summed[year] == pytest.approx(sums, rel=1e-6, abs=1e-6)
            assert totals[year] == pytest.approx(summed[year], rel=1e-6, abs=1e-6)
            if year > PROJECTION_END_YEAR:
                growth = _growth(totals_only, projected_with, year)
                assert totals[year] == pytest.approx(
                    totals[PROJECTION_END_YEAR] * growth, rel=1e-6
                )
    # Capital reads the totals compared above in every year; these years
    # cover the data year, both sides of the horizon and the last year.
    for name in MEANS_TEST_CAPITAL:
        for year in CAPITAL_YEARS:
            assert totals_only.calculate(name, year) == pytest.approx(
                balances_only.calculate(name, year), rel=1e-5, abs=1e-3
            ), (name, year)
