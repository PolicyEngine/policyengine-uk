"""Means tests deduct income tax before the winter fuel payment charge.

The charge (ITEPA 2003 s.681I) recovers a person's winter fuel payment
through income tax when their own total income exceeds £35,000 and they are
not entitled to a relevant benefit, Pension Credit and Universal Credit among
them. It depends on those benefits, so a means test that deducted income tax
after the charge would be circular: review r12 of #2066 found Pension
Credit's earnings rules (#2019) raising CycleError for a 70-year-old with
£2,000 of earnings. Every means test deducts the tax before the charge
(income_tax_before_winter_fuel_payment_charge) instead.

Invariants, in 2025 and 2026, for single people and couples of any mix of
ages around State Pension age, who rent from the council in England, Wales or
Scotland under each country's national schemes, with earnings, profits,
pensions, savings interest and property income (with no finance costs, so no
one weighs the property allowance against expenses), comparing the model
with the charge in effect against the same households with it repealed:

1. Every household computes: no means test is circular.
2. Differential: every means-tested benefit and the income each assesses
   (Pension Credit with its earnings tax and disregards, Housing Benefit,
   Council Tax Reduction, Universal Credit, the legacy income-related
   benefits and tax credits) is the same with and without the charge.
3. The winter fuel payments and income tax before the charge are the same
   with and without it, and income tax with the charge exceeds income tax
   without it by exactly the charge.
4. Household net income with the charge is household net income without it
   less the household's charges.

The pinned example is a couple aged 70 on council rent in Maidstone. The
first partner's £36,000 private pension is over the threshold, and neither
partner is on a relevant benefit, so the first partner repays their £100
share of the couple's £200 payment while the couple get Housing Benefit.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

REPEAL = {
    "gov.hmrc.income_tax.charges.winter_fuel_payment.in_effect": {
        "2025-01-01.2100-12-31": False
    }
}
# Local authorities without a modelled local council tax reduction scheme, so
# each country's national scheme applies.
LOCAL_AUTHORITIES = {
    "ENGLAND": "MAIDSTONE",
    "WALES": "CARDIFF",
    "SCOTLAND": "GLASGOW_CITY",
}
# Either side of State Pension age (66), of 75 (pension relief) and of 80
# (the higher winter fuel payment); a couple with a member under State
# Pension age claims Universal Credit.
AGES = [60, 65, 66, 70, 75, 80, 85]
# Amounts either side of the £35,000 threshold, alone or combined, and of the
# allowances and disregards.
EMPLOYMENT = [0, 0, 2_000, 15_000, 36_000]
PROFITS = [0, 0, 3_000, 20_000]
PRIVATE_PENSIONS = [0, 10_000, 30_000, 34_000, 36_000]
STATE_PENSIONS = [0, 9_000, 12_000]
SAVINGS_INTEREST = [0, 500, 3_000]
PROPERTY_INCOME = [0, 800, 8_000]
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

BENUNIT_VARIABLES = [
    "pension_credit_income",
    "pension_credit_employment_income_tax",
    "pension_credit_self_employment_income_tax",
    "pension_credit_earnings_disregard",
    "guarantee_credit",
    "savings_credit",
    "pension_credit",
    "housing_benefit_applicable_income",
    "housing_benefit",
    "council_tax_reduction_applicable_income",
    "council_tax_benefit",
    "universal_credit",
    "income_support",
    "esa_income",
    "jsa_income",
    "tax_credits",
]
# Person-level values the charge must not move.
PERSON_VARIABLES = [
    "winter_fuel_payment",
    "pension_age_winter_heating_payment",
    "income_tax_before_winter_fuel_payment_charge",
]
CHARGE = "winter_fuel_payment_charge"


@st.composite
def adult(draw):
    return dict(
        age=draw(st.sampled_from(AGES)),
        employment_income=draw(st.sampled_from(EMPLOYMENT)),
        self_employment_income=draw(st.sampled_from(PROFITS)),
        private_pension_income=draw(st.sampled_from(PRIVATE_PENSIONS)),
        state_pension=draw(st.sampled_from(STATE_PENSIONS)),
        savings_interest_income=draw(st.sampled_from(SAVINGS_INTEREST)),
        property_income=draw(st.sampled_from(PROPERTY_INCOME)),
    )


@st.composite
def family(draw):
    return dict(
        adults=[draw(adult()) for _ in range(draw(st.integers(1, 2)))],
        country=draw(st.sampled_from(sorted(LOCAL_AUTHORITIES))),
        rent=draw(st.sampled_from([3_000, 8_000, 20_000])),
        council_tax=draw(st.sampled_from([1_000, 2_500])),
        savings=draw(st.sampled_from([0, 6_000])),
    )


PINNED_COUPLE = dict(
    adults=[
        dict(
            age=70,
            employment_income=0,
            self_employment_income=0,
            private_pension_income=36_000,
            state_pension=0,
            savings_interest_income=0,
            property_income=0,
        ),
        dict(
            age=70,
            employment_income=0,
            self_employment_income=0,
            private_pension_income=0,
            state_pension=0,
            savings_interest_income=0,
            property_income=0,
        ),
    ],
    country="ENGLAND",
    rent=20_000,
    council_tax=2_500,
    savings=0,
)


def situation(families, year):
    people, benunits, households = {}, {}, {}
    for i, fam in enumerate(families):
        names = []
        for j, a in enumerate(fam["adults"]):
            name = f"p{i}_{j}"
            people[name] = {variable: {year: value} for variable, value in a.items()}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "country": {year: fam["country"]},
            "local_authority": {year: LOCAL_AUTHORITIES[fam["country"]]},
            "tenure_type": {year: "RENT_FROM_COUNCIL"},
            "rent": {year: fam["rent"]},
            "council_tax": {year: fam["council_tax"]},
            "savings": {year: fam["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def outcomes(families, year, reform=None):
    simulation = Simulation(situation=situation(families, year), reform=reform)

    def values(variable, **kwargs):
        return np.asarray(simulation.calculate(variable, year, **kwargs), dtype=float)

    result = {
        variable: values(variable)
        for variable in BENUNIT_VARIABLES
        + PERSON_VARIABLES
        + ["income_tax", CHARGE, "household_net_income"]
    }
    result["household_charge"] = values(CHARGE, map_to="household")
    return result


@PROPERTY_SETTINGS
@example([PINNED_COUPLE], 2026)
@given(st.lists(family(), min_size=1, max_size=6), st.sampled_from([2025, 2026]))
def test_means_tests_never_see_the_charge(families, year):
    charged = outcomes(families, year)
    repealed = outcomes(families, year, REPEAL)
    for variable in BENUNIT_VARIABLES + PERSON_VARIABLES:
        assert np.allclose(charged[variable], repealed[variable], atol=0.01), (
            variable,
            charged[variable],
            repealed[variable],
            families,
        )
    charge = charged[CHARGE]
    assert (repealed[CHARGE] == 0).all()
    assert np.allclose(
        charged["income_tax"] - repealed["income_tax"], charge, atol=0.01
    ), (charge, families)
    assert np.allclose(
        repealed["household_net_income"] - charged["household_net_income"],
        charged["household_charge"],
        atol=0.01,
    ), (charged["household_charge"], families)
    if families == [PINNED_COUPLE]:
        # Total income £36,000 over £35,000, and no relevant benefit: the
        # first partner repays their £100 shared amount (SI 2025/969).
        assert charge.tolist() == [100, 0]
        assert charged["pension_credit"][0] == 0
        assert charged["housing_benefit"][0] > 0
