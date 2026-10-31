"""The winter fuel payment charge never exceeds its ceiling.

The property allowance election (uses_property_allowance) settles a choice on
income tax before the charge wherever the most the charge could be on either
route (winter_fuel_payment_charge_ceiling) cannot reverse it. That is the
choice income tax including the charge gives only if, for every person on
every route, the charge is between nothing and the ceiling, and nothing where
the ceiling is nothing.

Invariants, in 2025 and 2026, for households of one or two families in each
of the four countries, with adults either side of State Pension age and of 80,
total income either side of £35,000, Pension Credit and Universal Credit
claimed or not, and landlords with and without finance costs, on the model's
own routes and with everyone using the property allowance or nobody:

1. The charge is never negative and never more than the ceiling.
2. Where the ceiling is nothing, so is the charge.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
AGES = [50, 65, 66, 70, 79, 80, 85]
PENSIONS = [0, 11_500, 34_000, 35_000, 36_000, 60_000]
PROPERTY_RECEIPTS = [0, 900, 3_300, 12_000]
FINANCE_COSTS = [0, 675, 1_200, 6_000]
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ROUTES = [None, True, False]


@st.composite
def adult(draw):
    receipts = draw(st.sampled_from(PROPERTY_RECEIPTS))
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


def situation(households, year, uses_allowance):
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
                if uses_allowance is not None:
                    people[name]["uses_property_allowance"] = {year: uses_allowance}
                names.append(name)
            benunits[f"b{h}_{f}"] = {
                "members": names,
                "would_claim_pc": {year: family["claims_pc"]},
                "would_claim_uc": {year: family["claims_uc"]},
            }
            members += names
        homes[f"h{h}"] = {"members": members, "country": {year: home["country"]}}
    return {"people": people, "benunits": benunits, "households": homes}


@PROPERTY_SETTINGS
@given(st.lists(household(), min_size=1, max_size=4), st.sampled_from([2025, 2026]))
def test_the_charge_never_exceeds_its_ceiling(households, year):
    for uses_allowance in ROUTES:
        simulation = Simulation(situation=situation(households, year, uses_allowance))
        charge = np.asarray(simulation.calculate("winter_fuel_payment_charge", year))
        ceiling = np.asarray(
            simulation.calculate("winter_fuel_payment_charge_ceiling", year)
        )
        assert (charge >= 0).all(), (uses_allowance, charge, households)
        assert (charge <= ceiling + 1e-4).all(), (uses_allowance, charge, ceiling)
        assert (charge[ceiling == 0] == 0).all(), (uses_allowance, charge, ceiling)
