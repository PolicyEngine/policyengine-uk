"""Property-based tests for the legacy means tests' pension contribution shares.

Each scheme's regulations state their own share of pension contributions to
deduct from earnings, one-half in every scheme modelled, and none refers to
another scheme's:

- Housing Benefit: SI 2006/213 regs 36(3)(b)-(c) and 38; SI 2006/214 regs
  36(2)(b)-(c) and 39 (gov.dwp.housing_benefit.means_test);
- Income Support: SI 1987/1967 regs 36(3)(b) and 38 (gov.dwp.income_support);
- Council Tax Reduction, each scheme under gov.local_authorities:
  the England pensioner scheme (SI 2012/2885 Sch 1 paras 19 and 29), Wales
  (WSI 2013/3029 Sch 1 paras 13 and 23, Sch 6 paras 15 and 24), Scotland (SSI
  2012/319 regs 33 and 36, SSI 2021/249 regs 50 and 51(9)), the working-age
  schemes of Merton, Kingston upon Thames, Newham, Westminster and Oxford, and
  the England default scheme (SI 2012/2886 Sch paras 42, 52 and 61) for every
  other family.

Invariants, for any generated population of families whose floors are slack
(earnings of at least 15,000 per adult and contributions of at most a fifth of
them, so no net-earnings, disregard or applicable-income floor binds, and no
Pension Credit or Universal Credit claim):

1. Exactness: when each scheme's share moves from 0.5 to r, the scheme's
   applicable income falls by exactly the family's contributions x (r - 0.5),
   and so do the scheme's net earnings.
2. Locality: every share is drawn distinct, so a family that read another
   scheme's share (or Housing Benefit's) would miss invariant 1. Pensioners in
   Merton follow the England pensioner scheme, not Merton's, and families in
   Northern Ireland, which has no Council Tax Reduction, read the England
   default scheme's share. An explicit example puts a contributing family on
   every route, so each is tested whatever else Hypothesis draws.
3. The pensioner earnings disregards do not move when the disregard caps are
   slack.
4. Differential: at current law Council Tax Reduction net earnings equal
   Housing Benefit net earnings, as both deduct half.
5. Current law: every share is 0.5 in every financial year from 2015 (the
   first year the model simulates) to 2030, Income Support's and Housing
   Benefit's too.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

CTR = "gov.local_authorities.{}.council_tax_reduction{}.means_test.pension_contribution_deduction_rate"
PARAMETERS = {
    "england_pensioner": CTR.format("england", ".pensioners"),
    "england_default": CTR.format("england", ".default_scheme"),
    "scotland": CTR.format("scotland", ""),
    "wales": CTR.format("wales", ""),
    "merton": CTR.format("merton", ""),
    "kingston_upon_thames": CTR.format("kingston_upon_thames", ""),
    "newham": CTR.format("newham", ""),
    "westminster": CTR.format("westminster", ""),
    "oxford": CTR.format("oxford", ""),
    "housing_benefit": (
        "gov.dwp.housing_benefit.means_test.pension_contribution_deduction_rate"
    ),
    "income_support": (
        "gov.dwp.income_support.means_test.pension_contribution_deduction_rate"
    ),
}
# Each route: (country, local authority, pension age, the share it reads).
ROUTES = {
    "england_pensioner": ("ENGLAND", "MAIDSTONE", True, "england_pensioner"),
    "merton_pensioner": ("ENGLAND", "MERTON", True, "england_pensioner"),
    "england_default": ("ENGLAND", "MAIDSTONE", False, "england_default"),
    "scotland_pension_age": ("SCOTLAND", "GLASGOW_CITY", True, "scotland"),
    "scotland_working_age": ("SCOTLAND", "GLASGOW_CITY", False, "scotland"),
    "wales_pension_age": ("WALES", "CARDIFF", True, "wales"),
    "wales_working_age": ("WALES", "CARDIFF", False, "wales"),
    "merton": ("ENGLAND", "MERTON", False, "merton"),
    "kingston_upon_thames": (
        "ENGLAND",
        "KINGSTON_UPON_THAMES",
        False,
        "kingston_upon_thames",
    ),
    "newham": ("ENGLAND", "NEWHAM", False, "newham"),
    "westminster": ("ENGLAND", "WESTMINSTER", False, "westminster"),
    "oxford": ("ENGLAND", "OXFORD", False, "oxford"),
    "northern_ireland": ("NORTHERN_IRELAND", "BELFAST", False, "england_default"),
}
# State Pension age is 66 to 67 over the years tested, so 68 and over is
# pension age and 55 and under working age.
WORKING_AGE = (25, 55)
PENSION_AGE = (68, 90)
# Shares other than 0.5, on a grid of twentieths so that every pair differs
# by at least 0.05. The model holds the share as float32 (0.05 reads back as
# 0.0500000007), so shares are compared within RATE_TOLERANCE.
SHARES = [i / 20 for i in range(21) if i != 10]
TOLERANCE = 0.05
RATE_TOLERANCE = 1e-6


@st.composite
def families(draw):
    route = draw(st.sampled_from(sorted(ROUTES)))
    pension_age = ROUTES[route][2]
    low, high = PENSION_AGE if pension_age else WORKING_AGE
    head_age = draw(st.integers(low, high))
    adults = []
    for _ in range(draw(st.integers(1, 2))):
        earnings = draw(st.floats(15_000, 60_000, allow_nan=False))
        share = draw(st.one_of(st.just(0.0), st.floats(0.01, 0.2)))
        # Partners within five years of each other, so neither is presumed
        # the other's child.
        age = draw(st.integers(max(low, head_age - 5), min(high, head_age + 5)))
        adults.append(
            dict(
                age=age,
                employment_income=earnings,
                personal_pension_contributions=round(earnings * share, 2),
            )
        )
    return dict(route=route, adults=adults)


@st.composite
def reforms(draw):
    shares = draw(
        st.lists(
            st.sampled_from(SHARES),
            min_size=len(PARAMETERS),
            max_size=len(PARAMETERS),
            unique=True,
        )
    )
    return dict(zip(PARAMETERS, shares))


def situation(units, year):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        country, local_authority, _, _ = ROUTES[unit["route"]]
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {key: {year: value} for key, value in adult.items()}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: False},
            "would_claim_pc": {year: False},
            "income_support": {year: 0.0},
            "jsa_income": {year: 0.0},
            "esa_income": {year: 0.0},
        }
        households[f"h{i}"] = {
            "members": names,
            "country": {year: country},
            "local_authority": {year: local_authority},
            "savings": {year: 0.0},
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "council_tax_reduction_pension_contribution_deduction_rate",
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_net_earnings",
    "council_tax_reduction_pensioner_earnings_disregard",
    "council_tax_reduction_pensioner",
    "income_support_applicable_income",
    "housing_benefit_net_earnings",
]


def calculate(units, year, reform=None):
    sim = Simulation(situation=situation(units, year), reform=reform)
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in VARIABLES}


def contributions(unit):
    return sum(adult["personal_pension_contributions"] for adult in unit["adults"])


def every_route():
    """One contributing family on each route, a couple on one of them, so that
    every route is tested whatever Hypothesis draws."""
    units = []
    for route in sorted(ROUTES):
        age = 70 if ROUTES[route][2] else 40
        adult = dict(
            age=age, employment_income=20_000.0, personal_pension_contributions=2_000.0
        )
        units.append(dict(route=route, adults=[adult]))
    # A partner two years older, in the same age band as the head.
    partner_age = units[0]["adults"][0]["age"] + 2
    units[0]["adults"].append(
        dict(
            age=partner_age,
            employment_income=30_000.0,
            personal_pension_contributions=1_500.0,
        )
    )
    return units


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=26),
    reforms(),
    st.sampled_from([2026, 2028, 2030]),
)
@example(
    units=every_route(),
    shares=dict(zip(PARAMETERS, SHARES)),
    year=2026,
)
def test_each_scheme_moves_by_contributions_times_its_own_change_in_share(
    units, shares, year
):
    base = calculate(units, year)
    reform = {PARAMETERS[key]: {str(year): share} for key, share in shares.items()}
    moved = calculate(units, year, reform)
    for i, unit in enumerate(units):
        country, _, pension_age, scheme = ROUTES[unit["route"]]
        c = contributions(unit)
        case = (unit, shares, year)
        # The route is the one intended: pension-age families in Great
        # Britain are the schemes' pensioners.
        in_great_britain = country != "NORTHERN_IRELAND"
        pensioner = base["council_tax_reduction_pensioner"][i]
        assert bool(pensioner) == (pension_age and in_great_britain), case
        # Floors are slack: income stays positive on both sides.
        for values in (base, moved):
            assert values["council_tax_reduction_applicable_income"][i] > 0, case
            assert values["income_support_applicable_income"][i] > 0, case
        rate = "council_tax_reduction_pension_contribution_deduction_rate"
        assert base[rate][i] == 0.5, case
        assert abs(moved[rate][i] - shares[scheme]) < RATE_TOLERANCE, case
        # Invariant 1 (with 2): exactly contributions x the scheme's change.
        for variable, share in (
            ("council_tax_reduction_applicable_income", shares[scheme]),
            ("council_tax_reduction_net_earnings", shares[scheme]),
            ("income_support_applicable_income", shares["income_support"]),
            ("housing_benefit_net_earnings", shares["housing_benefit"]),
        ):
            change = base[variable][i] - moved[variable][i]
            assert abs(change - c * (share - 0.5)) < TOLERANCE, (variable, case)
        # Invariant 3: slack caps leave the disregards where they were.
        disregard = "council_tax_reduction_pensioner_earnings_disregard"
        assert abs(base[disregard][i] - moved[disregard][i]) < TOLERANCE, case
        # Invariant 4: equal shares, equal net earnings.
        assert (
            abs(
                base["council_tax_reduction_net_earnings"][i]
                - base["housing_benefit_net_earnings"][i]
            )
            < TOLERANCE
        ), case


def test_every_share_is_one_half_in_every_year():
    for year in range(2015, 2031):
        # Read in each financial year (30 April, the model's convention).
        parameters = system.parameters(f"{year}-04-30")
        for key, path in PARAMETERS.items():
            node = parameters
            for name in path.split("."):
                node = getattr(node, name)
            assert node == 0.5, (key, year)
