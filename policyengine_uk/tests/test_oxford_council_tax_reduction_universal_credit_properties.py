"""Property-based tests for Oxford's Council Tax Reduction for applicants who
receive Universal Credit.

Oxford's Council Tax Reduction Scheme 2026 to 2027 bands a working-age
applicant who receives Universal Credit on Appendix 3's income: net earned
income as DWP provides it, plus the Universal Credit awarded, plus other
unearned income counted weekly, ignoring £48.15 a week of each carer element
and £84.46 a week of each disabled child element. Appendix 3 takes "All
other unearned income" into account, and Appendix 5's Child Benefit and
child maintenance disregards apply only to applicants without Universal
Credit; Part 1 para 30 and Annex 7 treat income derived from capital as
capital. Paragraphs 14 to 27, whose para 18 deducts half of pension
contributions, apply only to applicants without Universal Credit. DWP's net
earned income deducts relievable pension contributions in full (UC Regs 2013
reg 55(5)(a)). The model holds the 2026-27 scheme and applies Appendix 3
from April 2026.

Invariants, for any generated population of working-age Oxford families (one
or two adults, earnings, occupational pension contributions, spousal and
child maintenance, savings interest, capital, housing costs, children with
or without a disabled child addition, carers), over the families whose
applicant has a Universal Credit award:

1. Locality: a reform of Oxford's pension contribution share leaves every
   such family's Oxford reduction unchanged, while every Oxford family reads
   the reform's share.
2. Appendix 3 income: other income is Child Benefit at HMRC's 2026-27 rates
   plus child and spousal maintenance, with no interest and no assumed yield
   from capital. The income is DWP's net earned income plus that other
   income plus the award before deductions for debts less the element
   disregards, never below the first two. The disregards come off the award
   but not below nil: the award or, if less, 48.15 a week of each carer
   element up to the element plus 84.46 a week of each disabled child's
   addition up to the addition, with the additions at DWP's 2026-27 rates.
3. Bands: the reduction is the council tax share times the rate that the
   scheme's band table (weekly income up to 480.00, 530.00, 580.00 and
   660.00) gives for a fifty-second of the Appendix 3 income.
4. Pound for pound: while the award stays above nil after the disregards
   and no benefit cap applies, £520 more of spousal maintenance or private
   pension, which Universal Credit deducts in full, leaves the income
   unchanged, because the award falls by £520. £520 more of child
   maintenance or Child Benefit, which Universal Credit does not deduct,
   raises it by £520. £520 more interest leaves it unchanged. £1,000 more
   capital lowers it by exactly the rise in Universal Credit's assumed
   yield, which comes off the award and is not added back.
5. Monotonicity: more pension contributions never lower the reduction of a
   family that keeps its award, since each pound contributed lowers DWP's
   net earned income and raises the award by at most the 55% taper.
6. Differential: for families without a carer or disabled child element,
   the Appendix 3 income less any deductions for debts, with Universal
   Credit's unearned income in place of Oxford's other income, equals the
   Universal Credit income on which Merton, Kingston upon Thames, Newham and
   Westminster assess the same family, recovered from each council's award
   (they count the award after those deductions).
7. Earlier years: in 2025, before the scheme the model holds, the reduction
   of such a family is the band of its paragraphs 14 to 27 income less Child
   Benefit, with no tariff income, as before Appendix 3 was encoded.

The YAML cases in policy/baseline/gov/local_authorities/oxford/
council_tax_reduction/ pin the paragraphs 14 to 27 route and the hand-worked
Appendix 3 amounts. A differential against an earlier version of the model,
for families without Universal Credit, needs both versions installed, so it
runs outside the suite.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2026
EARLIER_YEAR = 2025
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
# HMRC's 2026-27 Child Benefit, a week: the eldest child and each other child.
# Earnings here stay below the High Income Child Benefit Charge threshold.
CHILD_BENEFIT = (27.05, 17.90)
# Float32 storage: amounts of tens of thousands carry errors of about 0.004.
TOLERANCE = 0.05
# The receipts and capital the pound-for-pound invariant adds.
STEP = 520.0
CAPITAL_STEP = 1_000.0

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
                maintenance_income=draw(st.sampled_from([0.0, 0.0, 1_300.0, 2_600.0])),
                savings_interest_income=draw(st.sampled_from([0.0, 0.0, 520.0])),
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
        # Capital within Oxford's and Universal Credit's 16,000 limits, some
        # above Universal Credit's 6,000 tariff threshold.
        savings=draw(st.sampled_from([0.0, 0.0, 6_000.0, 9_000.0, 12_000.0])),
    )


def situation(units, local_authorities=None, council_tax=COUNCIL_TAX, year=YEAR):
    """One household for each family, in Oxford unless local_authorities
    names each household's council."""
    local_authorities = local_authorities or ["OXFORD"] * len(units)
    people, benunits, households = {}, {}, {}
    for i, (unit, local_authority) in enumerate(zip(units, local_authorities)):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {key: {year: value} for key, value in adult.items()}
            names.append(name)
        for j, child in enumerate(unit["children"]):
            name = f"c{i}_{j}"
            people[name] = {"age": {year: child["age"]}}
            if child["disability"] is not None:
                people[name]["is_disabled_for_benefits"] = {year: True}
                people[name]["meets_uc_higher_disabled_child_condition"] = {
                    year: child["disability"] == "higher"
                }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: True},
            "claims_all_entitled_benefits": {year: True},
            "uc_housing_costs_element": {year: unit["housing"]},
            "uc_deduction_rate": {year: unit.get("deduction_rate", 0.0)},
        }
        if "child_benefit" in unit:
            benunits[f"b{i}"]["child_benefit"] = {year: unit["child_benefit"]}
        households[f"h{i}"] = {
            "members": names,
            "country": {year: "ENGLAND"},
            "local_authority": {year: local_authority},
            "council_tax": {year: council_tax},
            "savings": {year: unit.get("savings", 0.0)},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, variables, reform=None, year=YEAR, **kwargs):
    sim = Simulation(situation=situation(units, year=year, **kwargs), reform=reform)
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}


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


def child_benefit(unit):
    """A year of Child Benefit for the family's children, at HMRC's rates."""
    weekly = [
        CHILD_BENEFIT[0] if k == 0 else CHILD_BENEFIT[1]
        for k in range(len(unit["children"]))
    ]
    return sum(weekly) * WEEKS


def other_income(unit):
    """Appendix 3's other income from the family's own receipts: Child
    Benefit and child and spousal maintenance, but no interest (Annex 7)."""
    return child_benefit(unit) + sum(
        adult["maintenance_income"] + adult["spousal_maintenance_income"]
        for adult in unit["adults"]
    )


def example_families():
    """The YAML cases' families: each has an award, and between them they
    cover a carer, a lower-rate and a higher-rate disabled child, two
    disabled children, an award the carer disregard takes to nil, Child
    Benefit, child maintenance, interest and capital above the tariff
    threshold."""

    def adult(**extra):
        values = dict(
            age=35,
            employment_income=20_000.0,
            employee_pension_contributions=2_600.0,
            spousal_maintenance_income=0.0,
            maintenance_income=0.0,
            savings_interest_income=0.0,
            uc_carer_element_included_for_claimant=False,
        )
        return {**values, **extra}

    carer = dict(uc_carer_element_included_for_claimant=True)
    lone_parent = adult(
        employment_income=15_600.0,
        employee_pension_contributions=0.0,
        maintenance_income=2_600.0,
        savings_interest_income=520.0,
    )
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
        dict(
            adults=[lone_parent],
            children=[dict(age=5, disability=None), dict(age=8, disability=None)],
            housing=0.0,
            savings=11_250.0,
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
    "uc_benefit_cap_reduction_after_floor",
    "uc_tariff_income",
    "oxford_council_tax_reduction_universal_credit_other_income",
    "oxford_council_tax_reduction_universal_credit_income",
    "council_tax_reduction_maximum_eligible_liability",
    "council_tax_reduction_joint_liability_share",
    "oxford_council_tax_reduction_non_dep_deductions",
    "oxford_council_tax_reduction",
]


def disregards(values, i, unit):
    """Appendix 3's element disregards for family i, from DWP's 2026-27
    additions: 48.15 a week of each carer element and 84.46 a week of each
    disabled child's addition, each up to its element."""
    carers = sum(a["uc_carer_element_included_for_claimant"] for a in unit["adults"])
    carer_part = min(values["uc_carer_element"][i], carers * CARER_DISREGARD * WEEKS)
    child_part = sum(
        min(DISABLED_CHILD_ADDITION[c["disability"]], DISABLED_CHILD_DISREGARD) * WEEKS
        for c in unit["children"]
        if c["disability"] is not None
    )
    return carers, carer_part + child_part


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
        # Invariant 2: other income is the family's own receipts, worked from
        # its inputs and HMRC's Child Benefit rates, not Universal Credit's
        # unearned income.
        other = other_income(unit)
        assert (
            abs(
                values["oxford_council_tax_reduction_universal_credit_other_income"][i]
                - other
            )
            < TOLERANCE
        ), case
        # The award before deductions for debts come out of the payment.
        award = values["universal_credit"][i] + values["uc_deductions"][i]
        income = values["oxford_council_tax_reduction_universal_credit_income"][i]
        disabled_children = sum(c["disability"] is not None for c in unit["children"])
        carers, expected_ignored = disregards(values, i, unit)
        # The disregards come off the award only, not below nil, and never
        # exceed the elements or the weekly amounts.
        ignored = earned + other + award - income
        assert income >= max(0.0, earned + other) - TOLERANCE, case
        assert ignored >= -TOLERANCE, case
        assert ignored <= award + TOLERANCE, case
        elements = values["uc_carer_element"][i] + values["uc_disability_elements"][i]
        assert ignored <= elements + TOLERANCE, case
        weekly_cap = carers * CARER_DISREGARD + disabled_children * (
            DISABLED_CHILD_DISREGARD
        )
        assert ignored <= weekly_cap * WEEKS + TOLERANCE, case
        # The disregards exactly, from DWP's 2026-27 amounts.
        assert abs(ignored - min(award, expected_ignored)) < TOLERANCE, case
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


def raise_first_adult(unit, **changes):
    first = dict(unit["adults"][0])
    for key, change in changes.items():
        first[key] = first.get(key, 0.0) + change
    return dict(unit, adults=[first] + unit["adults"][1:])


# Each variant of a family: what changes, and how much Appendix 3 income it
# should add while the award stays above nil after the disregards.
VARIANTS = [
    # Universal Credit deducts spousal maintenance and private pensions in
    # full (reg 66(1)(a) and (d)), so the award falls by as much as Appendix
    # 3 adds.
    (
        "spousal maintenance",
        lambda u: raise_first_adult(u, spousal_maintenance_income=STEP),
        0.0,
    ),
    (
        "private pension",
        lambda u: raise_first_adult(u, private_pension_income=STEP),
        0.0,
    ),
    # Universal Credit does not count child maintenance or Child Benefit.
    (
        "child maintenance",
        lambda u: raise_first_adult(u, maintenance_income=STEP),
        STEP,
    ),
    ("Child Benefit", lambda u: dict(u, child_benefit=child_benefit(u) + STEP), STEP),
    # Income derived from capital is capital (Annex 7), and Universal Credit
    # does not count it.
    ("interest", lambda u: raise_first_adult(u, savings_interest_income=STEP), 0.0),
]
POUND_VARIABLES = INCOME_VARIABLES


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=4))
@example(units=example_families())
def test_pound_for_pound(units):
    variants = [make(unit) for _, make, _ in VARIANTS for unit in units]
    capital = [
        dict(unit, savings=unit.get("savings", 0.0) + CAPITAL_STEP) for unit in units
    ]
    values = calculate(units + variants + capital, POUND_VARIABLES)
    n = len(units)
    income = values["oxford_council_tax_reduction_universal_credit_income"]

    def award_above_nil(j, unit):
        # The award after the disregards stays above nil, and no benefit cap
        # applies, so a pound off the award is a pound off the income.
        award = values["universal_credit"][j] + values["uc_deductions"][j]
        return (
            has_award(values, j)
            and award - disregards(values, j, unit)[1] > TOLERANCE
            and values["uc_benefit_cap_reduction_after_floor"][j] == 0
        )

    for i, unit in enumerate(units):
        if not award_above_nil(i, unit):
            continue
        for k, (label, make, added) in enumerate(VARIANTS):
            j = (k + 1) * n + i
            if not award_above_nil(j, make(unit)):
                continue
            # Invariant 4.
            assert abs(income[j] - income[i] - added) < TOLERANCE, (label, unit)
        j = (len(VARIANTS) + 1) * n + i
        if award_above_nil(j, unit):
            # More capital raises Universal Credit's assumed yield, which
            # comes off the award and is not counted as income.
            yield_rise = values["uc_tariff_income"][j] - values["uc_tariff_income"][i]
            assert abs(income[i] - income[j] - yield_rise) < TOLERANCE, (
                "capital",
                unit,
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
            # Invariant 5.
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
    # No carer or disabled child: those disregards are Oxford's alone. No
    # capital: each council has its own capital rules.
    units = [
        dict(
            unit,
            savings=0.0,
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
            # which Oxford adds back, and Universal Credit's unearned income,
            # where Oxford counts its own other income.
            council_income = (
                values["oxford_council_tax_reduction_universal_credit_income"][i]
                - values["uc_deductions"][i]
                - values["oxford_council_tax_reduction_universal_credit_other_income"][
                    i
                ]
                + values["uc_unearned_income"][i]
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
            # Invariant 6. The withdrawal rate scales float32 errors in the
            # award by up to five.
            assert abs(income - council_income) < 5 * TOLERANCE, case


EARLIER_VARIABLES = [
    "universal_credit",
    "council_tax_reduction_head_applies_alone",
    "council_tax_reduction_applicable_income",
    "child_benefit",
    "council_tax_reduction_maximum_eligible_liability",
    "council_tax_reduction_joint_liability_share",
    "oxford_council_tax_reduction_non_dep_deductions",
    "oxford_council_tax_reduction",
]


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=8))
@example(units=example_families())
def test_earlier_years_keep_the_paragraphs_14_to_27_income(units):
    values = calculate(units, EARLIER_VARIABLES, year=EARLIER_YEAR)
    for i, unit in enumerate(units):
        if not has_award(values, i):
            continue
        # Invariant 7: before April 2026 an applicant with an award keeps the
        # paragraphs 14 to 27 income, less Child Benefit, with no tariff
        # income from capital.
        weekly = (
            max(
                0.0,
                values["council_tax_reduction_applicable_income"][i]
                - values["child_benefit"][i],
            )
            / WEEKS
        )
        liability = (
            values["council_tax_reduction_maximum_eligible_liability"][i]
            * values["council_tax_reduction_joint_liability_share"][i]
        )
        expected = max(
            0.0,
            liability * band_rate(weekly)
            - values["oxford_council_tax_reduction_non_dep_deductions"][i],
        )
        assert abs(values["oxford_council_tax_reduction"][i] - expected) < TOLERANCE, (
            unit
        )
