"""A branch holding some households gives them the whole simulation's values.

The property allowance election (uses_property_allowance) compares routes in
a branch holding only the households with someone choosing
(utils.household_subset), so that the comparisons cost in proportion to those
households. Households do not move each other's tax or benefits, except
through imputations spread over the whole population, which a subset takes
from it. So:

1. Each person's election and income tax are the same whether their household
   is simulated among others, some with no choice to make, or alone. The
   households are pensioners and landlords either side of the winter fuel
   payment charge's threshold, with finance costs near the property
   allowance, claiming Pension Credit and Universal Credit or not, so that
   some elections turn on the charge and so on benefits.
2. In a subset, each person has the value the whole simulation gives them,
   in its baseline too, and a data-built population's birthdays keep their
   places in the whole population's spread.
3. Each route the election compares is set on a branch holding only the
   households with a choice (PolicyEngine/policyengine-uk#2707).
"""

import numpy as np
import pandas as pd
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.household_subset import household_subset

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
