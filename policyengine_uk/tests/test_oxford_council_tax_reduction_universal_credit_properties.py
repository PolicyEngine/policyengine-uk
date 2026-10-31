"""Property-based tests for Oxford's Council Tax Reduction for applicants who
receive Universal Credit.

Oxford's Council Tax Reduction Scheme 2026 to 2027 bands a working-age
applicant who receives Universal Credit on Appendix 3's income: net earned
income as DWP provides it, plus the Universal Credit awarded, with other
income counted weekly, ignoring £48.15 a week of each carer element and
£84.46 a week of each disabled child element. Paragraphs 14 to 27, whose para
18 deducts half of pension contributions, apply only to applicants without
Universal Credit. DWP's net earned income deducts relievable pension
contributions in full (UC Regs 2013 reg 55(5)(a)).

Invariants, for any generated population of working-age Oxford families (one
or two adults, earnings, occupational pension contributions, maintenance,
housing costs, children with or without a disabled child addition, carers),
over the families whose applicant has a Universal Credit award:

1. Locality: a reform of Oxford's pension contribution share leaves every
   such family's Oxford reduction unchanged, while every Oxford family reads
   the reform's share.
2. Appendix 3 income: it is DWP's net earned income plus unearned income
   plus the award before deductions for debts, less the element disregards,
   never below the first two. The disregards come off the award but not
   below nil: the award or, if less, 48.15 a week of each carer element up
   to the element plus 84.46 a week of each disabled child's addition up to
   the addition, with the additions at DWP's 2026-27 rates.
3. Bands: the reduction is the council tax share times the rate that the
   scheme's band table (weekly income up to 480.00, 530.00, 580.00 and
   660.00) gives for a fifty-second of the Appendix 3 income.
4. Monotonicity: more pension contributions never lower the reduction of a
   family that keeps its award, since each pound contributed lowers DWP's
   net earned income and raises the award by at most the 55% taper.
5. Differential: for families without a carer or disabled child element,
   the Appendix 3 income less any deductions for debts equals the Universal
   Credit income on which Merton, Kingston upon Thames, Newham and
   Westminster assess the same family, recovered from each council's award
   (they count the award after those deductions).

The differential against origin/main for families without Universal Credit
lives outside the suite (see the pull request); here the YAML cases in
policy/baseline/gov/local_authorities/oxford/council_tax_reduction/ pin the
paragraphs 14 to 27 route.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
OXFORD_SHARE = (
    "gov.local_authorities.oxford.council_tax_reduction.means_test."
    "pension_contribution_deduction_rate"
)
COUNCIL_TAX = 1_800
WEEKS = 52
# The scheme's band table (Part 1 para 9 and Appendix 3): the top of each
# band's weekly income and its rate. Fractions of a penny between bands fall
# in the lower one, as the parameter's thresholds at 480.01, 530.01, 580.01
# and 660.01 place them.
BANDS = [(480.01, 1.0), (530.01, 0.75), (580.01, 0.5), (660.01, 0.25)]
CARER_DISREGARD = 48.15
DISABLED_CHILD_DISREGARD = 84.46
# DWP's 2026-27 disabled child additions, 164.79 and 514.71 a month, weekly.
DISABLED_CHILD_ADDITION = {"lower": 164.79 * 12 / 52, "higher": 514.71 * 12 / 52}
# Float32 storage: amounts of tens of thousands carry errors of about 0.004.
TOLERANCE = 0.05

money = st.floats(0, 40_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    adults = []
    for _ in range(draw(st.integers(1, 2))):
        earnings = draw(st.one_of(st.just(0.0), money))
        share = draw(st.one_of(st.just(0.0), st.floats(0.01, 0.2)))
        adults.append(
            dict(
                age=draw(st.integers(25, 55)),
                employment_income=earnings,
                employee_pension_contributions=round(earnings * share, 2),
                spousal_maintenance_income=draw(
                    st.sampled_from([0.0, 0.0, 1_000.0, 5_200.0])
                ),
                uc_carer_element_included_for_claimant=draw(
                    st.sampled_from([False, False, True])
                ),
            )
        )
    # Partners within five years of each other, so the model presumes neither
    # the other's child.
    if len(adults) == 2:
        adults[1]["age"] = min(55, max(25, adults[0]["age"] + 3))
    children = [
        dict(
            age=draw(st.integers(0, 15)),
            disability=draw(st.sampled_from([None, None, "lower", "higher"])),
        )
        for _ in range(draw(st.integers(0, 2)))
    ]
    return dict(
        adults=adults,
        children=children,
        housing=draw(st.sampled_from([0.0, 3_000.0, 7_000.0, 12_500.0, 15_000.0])),
        # Deductions for debts, as a share of the standard allowance.
        deduction_rate=draw(st.sampled_from([0.0, 0.0, 0.15])),
    )


def situation(units, local_authorities=None, council_tax=COUNCIL_TAX):
    """One household for each family, in Oxford unless local_authorities
    names each household's council."""
    local_authorities = local_authorities or ["OXFORD"] * len(units)
    people, benunits, households = {}, {}, {}
    for i, (unit, local_authority) in enumerate(zip(units, local_authorities)):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {key: {YEAR: value} for key, value in adult.items()}
            names.append(name)
        for j, child in enumerate(unit["children"]):
            name = f"c{i}_{j}"
            people[name] = {"age": {YEAR: child["age"]}}
            if child["disability"] is not None:
                people[name]["is_disabled_for_benefits"] = {YEAR: True}
                people[name]["meets_uc_higher_disabled_child_condition"] = {
                    YEAR: child["disability"] == "higher"
                }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {YEAR: True},
            "claims_all_entitled_benefits": {YEAR: True},
            "uc_housing_costs_element": {YEAR: unit["housing"]},
            "uc_deduction_rate": {YEAR: unit.get("deduction_rate", 0.0)},
        }
        households[f"h{i}"] = {
            "members": names,
            "country": {YEAR: "ENGLAND"},
            "local_authority": {YEAR: local_authority},
            "council_tax": {YEAR: council_tax},
            "savings": {YEAR: 0.0},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, variables, reform=None, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs), reform=reform)
    return {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in variables}


def band_rate(weekly_income):
    for top, rate in BANDS:
        if weekly_income < top:
            return rate
    return 0.0


def has_award(values, i):
    return (
        values["universal_credit"][i] > 0
        and not values["council_tax_reduction_head_applies_alone"][i]
    )


def example_families():
    """The YAML cases' families: each has an award, and between them they
    cover a carer, a lower-rate and a higher-rate disabled child, two
    disabled children and an award the carer disregard takes to nil."""

    def adult(**extra):
        values = dict(
            age=35,
            employment_income=20_000.0,
            employee_pension_contributions=2_600.0,
            spousal_maintenance_income=0.0,
            uc_carer_element_included_for_claimant=False,
        )
        return {**values, **extra}

    carer = dict(uc_carer_element_included_for_claimant=True)
    return [
        dict(adults=[adult()], children=[], housing=12_500.0),
        dict(adults=[adult(**carer)], children=[], housing=12_500.0),
        dict(adults=[adult(**carer)], children=[], housing=2_000.0),
        dict(
            adults=[adult()],
            children=[dict(age=5, disability="lower")],
            housing=7_000.0,
        ),
        dict(
            adults=[adult()],
            children=[
                dict(age=5, disability="higher"),
                dict(age=8, disability="lower"),
            ],
            housing=3_000.0,
        ),
    ]


LOCALITY_VARIABLES = [
    "universal_credit",
    "council_tax_reduction_head_applies_alone",
    "council_tax_reduction_pension_contribution_deduction_rate",
    "council_tax_reduction_applicable_income",
    "oxford_council_tax_reduction",
]


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=8),
    st.sampled_from([0.0, 0.25, 0.75, 1.0]),
)
@example(units=example_families(), share=0.0)
def test_oxford_pension_contribution_share_does_not_move_universal_credit_awards(
    units, share
):
    base = calculate(units, LOCALITY_VARIABLES)
    moved = calculate(units, LOCALITY_VARIABLES, {OXFORD_SHARE: {str(YEAR): share}})
    rate = "council_tax_reduction_pension_contribution_deduction_rate"
    for i, unit in enumerate(units):
        case = (unit, share)
        # The reform is live for every Oxford family.
        assert base[rate][i] == 0.5, case
        assert abs(moved[rate][i] - share) < 1e-6, case
        if has_award(base, i):
            # Invariant 1: the share does not reach an Appendix 3 award.
            assert (
                abs(
                    moved["oxford_council_tax_reduction"][i]
                    - base["oxford_council_tax_reduction"][i]
                )
                < TOLERANCE
            ), case


INCOME_VARIABLES = [
    "universal_credit",
    "uc_deductions",
    "council_tax_reduction_head_applies_alone",
    "uc_earned_income_before_work_allowance",
    "uc_unearned_income",
    "uc_carer_element",
    "uc_disability_elements",
    "oxford_council_tax_reduction_universal_credit_income",
    "council_tax_reduction_maximum_eligible_liability",
    "council_tax_reduction_joint_liability_share",
    "oxford_council_tax_reduction_non_dep_deductions",
    "oxford_council_tax_reduction",
]


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=8))
@example(units=example_families())
def test_appendix_3_income_and_band(units):
    values = calculate(units, INCOME_VARIABLES)
    for i, unit in enumerate(units):
        if not has_award(values, i):
            continue
        case = unit
        earned = values["uc_earned_income_before_work_allowance"][i]
        unearned = values["uc_unearned_income"][i]
        # The award before deductions for debts come out of the payment.
        award = values["universal_credit"][i] + values["uc_deductions"][i]
        income = values["oxford_council_tax_reduction_universal_credit_income"][i]
        carers = sum(
            a["uc_carer_element_included_for_claimant"] for a in unit["adults"]
        )
        disabled_children = sum(c["disability"] is not None for c in unit["children"])
        # Invariant 2: the disregards come off the award only, not below nil,
        # and never exceed the elements or the weekly amounts.
        ignored = earned + unearned + award - income
        assert income >= max(0.0, earned + unearned) - TOLERANCE, case
        assert ignored >= -TOLERANCE, case
        assert ignored <= award + TOLERANCE, case
        elements = values["uc_carer_element"][i] + values["uc_disability_elements"][i]
        assert ignored <= elements + TOLERANCE, case
        weekly_cap = carers * CARER_DISREGARD + disabled_children * (
            DISABLED_CHILD_DISREGARD
        )
        assert ignored <= weekly_cap * WEEKS + TOLERANCE, case
        # The disregards exactly, from DWP's 2026-27 amounts.
        carer_part = min(
            values["uc_carer_element"][i], carers * CARER_DISREGARD * WEEKS
        )
        child_part = sum(
            min(DISABLED_CHILD_ADDITION[c["disability"]], DISABLED_CHILD_DISREGARD)
            * WEEKS
            for c in unit["children"]
            if c["disability"] is not None
        )
        assert abs(ignored - min(award, carer_part + child_part)) < TOLERANCE, case
        # Invariant 3: the scheme's band table sets the reduction.
        liability = (
            values["council_tax_reduction_maximum_eligible_liability"][i]
            * values["council_tax_reduction_joint_liability_share"][i]
        )
        expected = max(
            0.0,
            liability * band_rate(income / WEEKS)
            - values["oxford_council_tax_reduction_non_dep_deductions"][i],
        )
        assert abs(values["oxford_council_tax_reduction"][i] - expected) < TOLERANCE, (
            case
        )


MONOTONE_VARIABLES = [
    "universal_credit",
    "council_tax_reduction_head_applies_alone",
    "oxford_council_tax_reduction",
]


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=8),
    st.floats(100, 5_000, allow_nan=False),
)
@example(units=example_families(), extra=1_300.0)
def test_more_pension_contributions_never_lower_the_reduction(units, extra):
    raised = []
    for unit in units:
        adults = [
            dict(
                adult,
                employee_pension_contributions=min(
                    adult["employment_income"],
                    adult["employee_pension_contributions"] + extra,
                ),
            )
            for adult in unit["adults"]
        ]
        raised.append(dict(unit, adults=adults))
    base = calculate(units, MONOTONE_VARIABLES)
    more = calculate(raised, MONOTONE_VARIABLES)
    for i, unit in enumerate(units):
        if has_award(base, i) and has_award(more, i):
            # Invariant 4.
            assert (
                more["oxford_council_tax_reduction"][i]
                >= base["oxford_council_tax_reduction"][i] - TOLERANCE
            ), (unit, extra)


OTHER_COUNCILS = {
    "MERTON": ("merton", "merton_council_tax_reduction"),
    "KINGSTON_UPON_THAMES": (
        "kingston_upon_thames",
        "kingston_upon_thames_council_tax_reduction",
    ),
    "NEWHAM": ("newham", "newham_council_tax_reduction"),
    "WESTMINSTER": ("westminster", "westminster_council_tax_reduction"),
}
# Council tax high enough that the other councils' awards stay above nil, so
# the test can read back from each award the income behind it.
LARGE_COUNCIL_TAX = 50_000


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=6))
@example(units=example_families()[:1])
def test_appendix_3_income_matches_the_other_councils_universal_credit_income(
    units,
):
    # No carer or disabled child: those disregards are Oxford's alone.
    units = [
        dict(
            unit,
            adults=[
                dict(adult, uc_carer_element_included_for_claimant=False)
                for adult in unit["adults"]
            ],
            children=[dict(child, disability=None) for child in unit["children"]],
        )
        for unit in units
    ]
    # Each family once in Oxford and once in each other council, in one
    # simulation: family i of council k is household k x len(units) + i.
    councils = ["OXFORD"] + list(OTHER_COUNCILS)
    values = calculate(
        units * len(councils),
        INCOME_VARIABLES
        + ["uc_maximum_amount"]
        + [variable for _, variable in OTHER_COUNCILS.values()],
        local_authorities=[c for c in councils for _ in units],
        council_tax=LARGE_COUNCIL_TAX,
    )
    parameters = system.parameters(f"{YEAR}-04-30").gov.local_authorities
    n = len(units)
    for k, authority in enumerate(councils[1:], start=1):
        key, variable = OTHER_COUNCILS[authority]
        ctr = getattr(parameters, key).council_tax_reduction
        for i, unit in enumerate(units):
            if not has_award(values, i):
                continue
            j = k * n + i
            case = (unit, authority)
            # The council's scheme sees the same award.
            assert (
                abs(values["universal_credit"][j] - values["universal_credit"][i])
                < TOLERANCE
            ), case
            liability = (
                values["council_tax_reduction_maximum_eligible_liability"][j]
                * values["council_tax_reduction_joint_liability_share"][j]
            )
            award = values[variable][j]
            # Those councils count the award after deductions for debts,
            # which Oxford adds back.
            council_income = (
                values["oxford_council_tax_reduction_universal_credit_income"][i]
                - values["uc_deductions"][i]
            )
            assert award > 0, case
            if award > liability * ctr.maximum_support_rate - TOLERANCE:
                # No income above the applicable amount to read back: the
                # Universal Credit income is at most the maximum amount.
                maximum_amount = values["uc_maximum_amount"][j]
                assert council_income < maximum_amount + TOLERANCE, case
                continue
            # award = liability x maximum rate - withdrawal rate x (income -
            # applicable amount), with the Universal Credit maximum amount as
            # the applicable amount (no non-dependants here).
            income = values["uc_maximum_amount"][j] + (
                liability * ctr.maximum_support_rate - award
            ) / (ctr.means_test.withdrawal_rate)
            # Invariant 5. The withdrawal rate scales float32 errors in the
            # award by up to five.
            assert abs(income - council_income) < 5 * TOLERANCE, case
