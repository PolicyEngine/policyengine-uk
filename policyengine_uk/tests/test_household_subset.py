"""A branch holding some households gives them the whole simulation's values.

The property allowance election (uses_property_allowance) compares routes in
a branch holding only the households with someone choosing
(utils.household_subset), so that the comparisons cost in proportion to those
households. Households do not move each other's tax or benefits, except
through the formulas that read beyond their own households
(WHOLE_POPULATION_VARIABLES). So:

1. Each person's election and income tax are the same whether their household
   is simulated among others, some with no choice to make, or alone. The
   households are pensioners and landlords either side of the winter fuel
   payment charge's threshold, with finance costs near the property
   allowance, claiming Pension Credit and Universal Credit or not, so that
   some elections turn on the charge and so on benefits. The same holds with
   labour supply responses.
2. In a subset, each person has the value the whole simulation gives them,
   in its baseline too, and a data-built population's birthdays keep their
   places in the whole population's spread.
3. Each route the election compares is set on a branch holding only the
   households with a choice (PolicyEngine/policyengine-uk#2707).
4. WHOLE_POPULATION_VARIABLES lists exactly the formulas that read beyond
   their own households directly, every walk up to an ancestor simulation
   has been reviewed, and a subset works out none of the listed formulas but
   those it takes from the whole population, under current law or with
   labour supply responses.
"""

import ast
import inspect
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.household_subset import (
    TAKEN_FROM_WHOLE_POPULATION,
    WHOLE_POPULATION,
    WHOLE_POPULATION_VARIABLES,
    household_subset,
)

COUNTRIES = ["ENGLAND", "SCOTLAND"]
AGES = [50, 66, 70, 80]
PENSIONS = [0, 11_500, 34_000, 35_000, 36_000, 60_000]
PROPERTY_RECEIPTS = [900, 2_000, 3_300, 12_000]
FINANCE_COSTS = [0, 675, 950, 1_200, 6_000]
SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
TAX = ["uses_property_allowance", "income_tax", "winter_fuel_payment_charge"]


@st.composite
def adult(draw):
    receipts = draw(st.sampled_from([0] + PROPERTY_RECEIPTS))
    return dict(
        age=draw(st.sampled_from(AGES)),
        private_pension_income=draw(st.sampled_from(PENSIONS)),
        employment_income=draw(st.sampled_from([0, 0, 20_000])),
        property_rental_income=receipts,
        property_income=receipts * draw(st.sampled_from([0.8, 0.95])),
        property_finance_costs=draw(st.sampled_from(FINANCE_COSTS)) if receipts else 0,
    )


@st.composite
def household(draw):
    families = [
        dict(
            adults=[draw(adult()) for _ in range(draw(st.integers(1, 2)))],
            claims_pc=draw(st.booleans()),
            claims_uc=draw(st.booleans()),
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    return dict(families=families, country=draw(st.sampled_from(COUNTRIES)))


# A pensioner household with no property, so no one in it chooses a route
# and the comparisons leave it out.
NO_CHOICE = dict(
    families=[
        dict(
            adults=[dict(age=70, private_pension_income=36_000)],
            claims_pc=True,
            claims_uc=False,
        )
    ],
    country="ENGLAND",
)


def landlord(costs, **income):
    """A landlord with receipts of £2,000, no expenses and the given finance
    costs, alone in an English household that would claim Pension Credit."""
    adult = dict(
        property_rental_income=2_000,
        property_income=2_000,
        property_finance_costs=costs,
        **income,
    )
    return dict(
        families=[dict(adults=[adult], claims_pc=True, claims_uc=False)],
        country="ENGLAND",
    )


# Two landlords who elect for partial relief, away from the default for
# receipts above the allowance. The first does so on tax before the winter
# fuel payment charge: the allowance saves £200 against £20 of finance-cost
# reduction. The second gives up £100 more tax before the charge, but
# expenses take their total income over £35,000 and so bring a £200 charge.
ELECTING = [
    landlord(100, age=40, employment_income=30_000),
    landlord(1_500, age=70, private_pension_income=33_500),
]


def situation(households, year):
    people, benunits, homes = {}, {}, {}
    for h, home in enumerate(households):
        members = []
        for f, family in enumerate(home["families"]):
            names = []
            for a, values in enumerate(family["adults"]):
                name = f"p{h}_{f}_{a}"
                people[name] = {
                    variable: {year: value} for variable, value in values.items()
                }
                names.append(name)
            benunits[f"b{h}_{f}"] = {
                "members": names,
                "would_claim_pc": {year: family["claims_pc"]},
                "would_claim_uc": {year: family["claims_uc"]},
            }
            members += names
        homes[f"h{h}"] = {"members": members, "country": {year: home["country"]}}
    return {"people": people, "benunits": benunits, "households": homes}


def results(simulation, year):
    return [np.asarray(simulation.calculate(name, year)) for name in TAX]


@SETTINGS
@given(st.lists(household(), min_size=2, max_size=3), st.sampled_from([2025, 2026]))
def test_the_election_does_not_depend_on_other_households(households, year):
    households = [NO_CHOICE] + ELECTING + households
    together = results(Simulation(situation=situation(households, year)), year)
    assert together[0][1:3].all()
    alone = [
        results(Simulation(situation=situation([home], year)), year)
        for home in households
    ]
    for k, name in enumerate(TAX):
        expected = np.concatenate([values[k] for values in alone])
        assert np.allclose(together[k], expected, atol=0.01), (name, households)


def test_routes_are_compared_on_only_the_households_with_a_choice(monkeypatch):
    # The pensioner landlord's choice turns on the winter fuel payment charge,
    # so comparing it works out the benefits the charge reads. Each route is
    # set on a branch of the one household with a choice, not of all three.
    routes_set = []
    set_input = Simulation.set_input

    def recording(simulation, variable_name, period, value):
        if variable_name == "uses_property_allowance":
            routes_set.append(len(value))
        return set_input(simulation, variable_name, period, value)

    monkeypatch.setattr(Simulation, "set_input", recording)
    households = [NO_CHOICE, NO_CHOICE, ELECTING[1]]
    simulation = Simulation(situation=situation(households, 2026))
    assert simulation.calculate("uses_property_allowance", 2026)[-1]
    assert routes_set and set(routes_set) == {1}, routes_set


def test_a_subset_gives_its_people_the_whole_simulations_values():
    households = [NO_CHOICE] + [
        dict(
            families=[
                dict(
                    adults=[
                        dict(
                            age=70,
                            private_pension_income=pension,
                            property_rental_income=2_000,
                            property_income=1_900,
                            property_finance_costs=950,
                        )
                    ],
                    claims_pc=True,
                    claims_uc=False,
                )
            ],
            country=country,
        )
        for pension, country in [(34_000, "ENGLAND"), (36_000, "SCOTLAND")]
    ]
    simulation = Simulation(
        situation=situation(households, 2026),
        reform={
            "gov.hmrc.income_tax.rates.uk[0].rate": {"2026-01-01.2100-12-31": 0.21}
        },
    )
    names = ["income_tax", "pension_credit", "winter_fuel_payment_charge"]
    whole = {name: np.asarray(simulation.calculate(name, 2026)) for name in names}
    baseline = np.asarray(simulation.baseline.calculate("income_tax", 2026))
    people = np.array([False, True, False])
    with household_subset(simulation, "test", people) as subset:
        assert subset.person.tolist() == [1]
        branch = subset.simulation
        assert branch.populations["household"].count == 1
        assert branch.baseline.populations["person"].count == 1
        for name in names:
            assert np.allclose(
                np.asarray(branch.calculate(name, 2026)), whole[name][[1]]
            ), name
        assert np.allclose(
            np.asarray(branch.baseline.calculate("income_tax", 2026)), baseline[[1]]
        )
    assert "test" not in simulation.branches
    assert "test" not in simulation.baseline.branches


def test_a_subset_keeps_birthdays_placed_in_the_whole_population():
    n = 60
    ids = np.arange(n)
    rng = np.random.default_rng(0)
    year = UKSingleYearDataset(
        person=pd.DataFrame(
            dict(
                person_id=ids,
                person_benunit_id=ids,
                person_household_id=ids,
                age=np.full(n, 66),
            )
        ),
        benunit=pd.DataFrame(dict(benunit_id=ids)),
        household=pd.DataFrame(
            dict(household_id=ids, household_weight=rng.lognormal(0, 1, n))
        ),
        fiscal_year=2025,
    )
    simulation = Microsimulation(dataset=UKMultiYearDataset(datasets=[year]))
    people = ids % 3 == 0
    with household_subset(simulation, "test", people) as subset:
        in_subset = np.asarray(
            subset.simulation.calculate("months_since_last_birthday", 2026)
        )
    whole = np.asarray(simulation.calculate("months_since_last_birthday", 2026))
    assert np.array_equal(in_subset, whole[people])


# Two people at work: a Scottish couple, one past State Pension age, who
# claim Pension Credit and Universal Credit, and someone on £30,000 alone.
COUPLE = dict(
    families=[
        dict(
            adults=[
                dict(age=40, employment_income=20_000),
                dict(age=67, private_pension_income=9_000, employment_income=6_000),
            ],
            claims_pc=True,
            claims_uc=True,
        )
    ],
    country="SCOTLAND",
)
EMPLOYED = dict(
    families=[
        dict(
            adults=[dict(age=40, employment_income=30_000)],
            claims_pc=False,
            claims_uc=False,
        )
    ],
    country="ENGLAND",
)
LABOUR_SUPPLY_RESPONSES = {
    "gov.simulation.labour_supply_responses.income_elasticity": {
        "2026-01-01.2100-12-31": -0.05
    },
    "gov.simulation.labour_supply_responses.substitution_elasticity": {
        "2026-01-01.2100-12-31": 0.25
    },
    "gov.hmrc.income_tax.rates.uk[0].rate": {"2026-01-01.2100-12-31": 0.21},
}


def test_labour_supply_responses_give_each_household_its_tax_alone():
    # The working landlord's earnings respond to the reform, and a subset
    # takes that response from the whole population.
    households = [EMPLOYED] + ELECTING
    year = 2026
    together = results(
        Simulation(
            situation=situation(households, year), reform=LABOUR_SUPPLY_RESPONSES
        ),
        year,
    )
    alone = [
        results(
            Simulation(
                situation=situation([home], year), reform=LABOUR_SUPPLY_RESPONSES
            ),
            year,
        )
        for home in households
    ]
    for k, name in enumerate(TAX):
        expected = np.concatenate([values[k] for values in alone])
        assert np.allclose(together[k], expected, atol=0.01), name


# Reading a population weight, ranking, taking a median or spreading records
# by weight reads the whole population, and response_source reads an ancestor
# simulation. A person's or benefit unit's weight is their household's, so
# the weights themselves read only it.
READS_BEYOND_HOUSEHOLDS = re.compile(
    r"""["'](household_weight|person_weight|benunit_weight)["']"""
    r"|stratified_uniform\(|decile_rank\(|\.median\(|percentile\(|response_source\("
)
WEIGHTS = {"household_weight", "person_weight", "benunit_weight"}


def test_every_formula_that_reads_beyond_its_households_is_listed():
    reading = set()
    for name, variable in CountryTaxBenefitSystem().variables.items():
        for formula in variable.formulas.values():
            if READS_BEYOND_HOUSEHOLDS.search(inspect.getsource(formula)):
                reading.add(name)
    assert reading - WEIGHTS == WHOLE_POPULATION_VARIABLES, (
        "Add a formula that reads beyond its own households to "
        "utils.household_subset.WHOLE_POPULATION_VARIABLES, or drop one that "
        "no longer does: missing "
        f"{sorted(reading - WEIGHTS - WHOLE_POPULATION_VARIABLES)}, stale "
        f"{sorted(WHOLE_POPULATION_VARIABLES - reading)}"
    )


# Each function that walks up the parent_branch chain, by file, and what it
# reads there: a calculation depth (Simulation.set_input) or branch names,
# which are the same in a household subset, or an ancestor's labour supply
# response (response_source), which a subset takes from the whole population
# instead.
REVIEWED_ANCESTOR_WALKS = {
    "simulation.py": {"set_input"},
    "utils/aggregate_impact/guard.py": {"_visible_branches"},
    "utils/labour_supply_responses.py": {"response_source"},
    "utils/supplied_inputs.py": {"_visible_branch_names"},
}


def test_every_walk_up_to_an_ancestor_simulation_is_reviewed():
    package = Path(policyengine_uk.__file__).parent
    walks = {}
    for path in sorted(package.rglob("*.py")):
        relative = path.relative_to(package).as_posix()
        if relative.startswith("tests/"):
            continue
        for function in ast.walk(ast.parse(path.read_text())):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                getattr(node, "attr", None) == "parent_branch"
                or (isinstance(node, ast.Constant) and node.value == "parent_branch")
                for node in ast.walk(function)
            ):
                walks.setdefault(relative, set()).add(function.name)
    assert walks == REVIEWED_ANCESTOR_WALKS, (
        "A function walks up to an ancestor simulation. If it reads the "
        "ancestor's values, a household subset (utils.household_subset) "
        "gets the whole population's: list the formulas that use it in "
        "WHOLE_POPULATION_VARIABLES, then add it here. Found "
        f"{walks}"
    )


@pytest.mark.parametrize(
    "reform",
    [None, LABOUR_SUPPLY_RESPONSES],
    ids=["current law", "labour supply responses"],
)
def test_a_subset_works_out_no_formula_that_reads_beyond_its_households(
    monkeypatch, reform
):
    # The pensioner landlord's choice turns on the winter fuel payment charge,
    # so the subset works out the charge and the relevant benefits it reads;
    # the couple claim them, and with labour supply responses earnings
    # respond to the reform.
    worked_out = set()
    run_formula = Simulation._run_formula

    def recording(simulation, variable, population, period):
        if getattr(simulation, WHOLE_POPULATION, None) is not None:
            worked_out.add(variable.name)
        return run_formula(simulation, variable, population, period)

    monkeypatch.setattr(Simulation, "_run_formula", recording)
    households = [NO_CHOICE, COUPLE, EMPLOYED] + ELECTING
    simulation = Simulation(situation=situation(households, 2026), reform=reform)
    simulation.calculate("income_tax", 2026)
    charge = {
        "winter_fuel_payment_charge",
        "is_on_pension_credit",
        "is_on_universal_credit",
    }
    assert charge <= worked_out
    read = worked_out & (WHOLE_POPULATION_VARIABLES - TAKEN_FROM_WHOLE_POPULATION)
    assert not read, (
        f"A household subset now works out {sorted(read)}, which read beyond "
        "their own households, so it would give them other values. Take "
        "their whole-population value in a subset, as "
        "months_since_last_birthday does, and list them in "
        "TAKEN_FROM_WHOLE_POPULATION."
    )
