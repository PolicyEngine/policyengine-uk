"""Carer Support Payment in Council Tax Reduction income.

Scottish carers receive Carer Support Payment in place of Carer's Allowance.
Council Tax Reduction income counted Carer's Allowance but left Carer Support
Payment out, so a Scottish carer's reduction was assessed as if the carer's
benefit were not paid. Scottish Council Tax Reduction counts the Carer Support
Payment component in full: the Council Tax Reduction (Scotland) Regulations
2021 (SSI 2021/249) reg 57(1)(b)(iva) at working age, and the Council Tax
Reduction (State Pension Credit) (Scotland) Regulations 2012 (SSI 2012/319)
reg 27(1)(j) at pension age.

Neither counts the Scottish Carer Supplement, paid with Carer Support Payment
from 15 March 2026: reg 57(1) is a closed list that leaves it out, and reg
27(1)(j)(xxib) excepts it. Nor does the tax on the supplement count: at
working age SSI 2021/249 deducts income tax only from earnings (Part 6
Chapter 3), and at pension age SSI 2012/319 reg 31(12) disregards the tax
payable on income taken into account, which the supplement is not. So in law
the supplement does not touch Council Tax Reduction at all. The model deducts
all of a family's income tax from its Council Tax Reduction income, an
existing approximation, so there the supplement, which is taxable (SI
2026/93), reaches that income through the tax charged on it and in no other
way.

Invariants, for single people and couples in Scotland in 2026 in which one
member is a carer, all of working age and taking no Universal Credit or all
over State Pension age:

1. Counts the component: claiming Carer Support Payment raises Council Tax
   Reduction income, before income tax and National Insurance and apart from
   the other benefits it counts, by exactly the Carer Support Payment
   component (86.45 a week), not by the component plus the supplement. For a
   carer who qualifies by caring hours, and so has the carer premium either
   way, the reduction itself never rises, and where both awards are partial
   it falls by 20% of the rise in income.
2. Invariant to the supplement: setting the Scottish Carer Supplement to zero
   leaves Carer Support Payment and the other benefits counted in Council
   Tax Reduction income (Child Benefit, the income-related benefits,
   Universal Credit and tax credits) unchanged, and changes that income only
   through income tax: income plus income tax is unchanged. The supplement never lowers the
   reduction, and where both awards are partial it raises it by 20% of the
   tax on the supplement.
3. Differential: Council Tax Reduction and Housing Benefit assess the same
   carer income. Where Guarantee Credit does not passport Housing Benefit,
   Housing Benefit applicable income, before its disregard, childcare element
   and tariff income, equals Council Tax Reduction income. This holds in
   Scotland, where the carer's benefit is Carer Support Payment, and in
   England and Wales, where it is Carer's Allowance.

Invariants 1 to 3 concern Council Tax Reduction income under the general rules.
A pension-age family in receipt of a guarantee credit has its whole income
disregarded (SSI 2012/319 reg 24), and one in receipt of savings credit only is
assessed on the Secretary of State's Pension Credit income plus the savings
credit (reg 25), so those cells are left out of 1 to 3 and checked instead by:

4. Pension Credit routes: where the family is in receipt of a guarantee credit,
   Council Tax Reduction income is nil; where it is in receipt of savings credit
   only, it equals Pension Credit income plus the Pension Credit paid.

These compare the model's own income measures, so they hold whatever carer's
benefit the model pays. The model does not yet reduce Carer Support Payment
by State Pension (the Carer's Assistance (Carer Support Payment) (Scotland)
Regulations 2023 reg 16(2)), and it applies the Housing Benefit applicable
amounts to every nation's Council Tax Reduction.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PENSIONS = np.arange(0, 40_001, 2_000)
WEEKS = 52
CARER_SUPPORT_PAYMENT = 86.45 * WEEKS
SCOTTISH_CARER_SUPPLEMENT = 11.70 * WEEKS
WITHDRAWAL_RATE = 0.2
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = {
    "ENGLAND": "NORTH_WEST",
    "WALES": "WALES",
    "SCOTLAND": "SCOTLAND",
}
NO_SCOTTISH_CARER_SUPPLEMENT = {
    "gov.social_security_scotland.carer_support_payment.supplement": {
        "2026-01-01.2100-12-31": 0
    }
}
# The benefits Council Tax Reduction income counts besides the personal ones.
OTHER_COUNTED_BENEFITS = [
    "child_benefit",
    "income_support",
    "jsa_income",
    "esa_income",
    "universal_credit",
    "tax_credits",
]
BENUNIT_VARIABLES = [
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_applicable_amount",
    "council_tax_benefit",
    "guarantee_credit",
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_applicable_income_childcare_element",
    "housing_benefit_tariff_income",
    "in_receipt_of_guarantee_credit",
    "in_receipt_of_savings_credit_only",
    "pension_credit_income",
    "pension_credit",
    *OTHER_COUNTED_BENEFITS,
]
PERSON_VARIABLES = [
    "carers_allowance",
    "carer_support_payment",
    "scottish_carer_supplement",
    "income_tax",
    "national_insurance",
]
CLAIMS = (True, False)
# A Scottish pensioner carer with no State Pension: across the private pension
# grid this family moves between the general rules and savings credit only.
SAVINGS_CREDIT_CARER = dict(
    pension_age=True,
    adults=[dict(age=80, state_pension=0.0)],
    carer=0,
    by_hours=True,
    country="SCOTLAND",
    council_tax=2_000.0,
)


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


@st.composite
def family(draw, countries=("SCOTLAND",)):
    pension_age = draw(st.booleans())
    adults = []
    for _ in range(draw(st.integers(1, 2))):
        if pension_age:
            adult = dict(
                age=draw(st.integers(67, 95)),
                state_pension=draw(money(15_000)),
            )
        else:
            adult = dict(
                age=draw(st.integers(25, 60)),
                employment_income=draw(st.one_of(st.just(0.0), money(30_000))),
            )
        adults.append(adult)
    return dict(
        pension_age=pension_age,
        adults=adults,
        carer=draw(st.integers(0, len(adults) - 1)),
        # The carer qualifies either by caring hours or by a reported award.
        by_hours=draw(st.booleans()),
        country=draw(st.sampled_from(countries)),
        council_tax=draw(st.floats(500, 3_000, allow_nan=False)),
    )


def situation(families):
    """Each family at each private pension, claiming and not claiming."""
    people, benunits, households = {}, {}, {}
    for i, fam in enumerate(families):
        for k, pension in enumerate(PENSIONS):
            for c, claims in enumerate(CLAIMS):
                names = []
                for j, a in enumerate(fam["adults"]):
                    name = f"p{i}_{k}_{c}_{j}"
                    person = {
                        "age": {YEAR: a["age"]},
                        "state_pension": {YEAR: a.get("state_pension", 0.0)},
                        "employment_income": {YEAR: a.get("employment_income", 0.0)},
                        # All private pension goes to the first adult.
                        "private_pension_income": {YEAR: float(pension) * (j == 0)},
                    }
                    if j == fam["carer"]:
                        if fam["by_hours"]:
                            person["care_hours"] = {YEAR: 35}
                        else:
                            person["carers_allowance_reported"] = {YEAR: 1}
                        person["would_claim_carers_allowance"] = {YEAR: claims}
                    people[name] = person
                    names.append(name)
                benunits[f"b{i}_{k}_{c}"] = {
                    "members": names,
                    "would_claim_uc": {YEAR: False},
                }
                households[f"h{i}_{k}_{c}"] = {
                    "members": names,
                    "country": {YEAR: fam["country"]},
                    "region": {YEAR: REGIONS[fam["country"]]},
                    "council_tax": {YEAR: fam["council_tax"]},
                    "savings": {YEAR: 0.0},
                }
    return {"people": people, "benunits": benunits, "households": households}


def grid(families, reform=None):
    """Arrays indexed by family, private pension and whether the carer claims
    (index 0 claims, index 1 does not)."""
    simulation = Simulation(situation=situation(families), reform=reform)
    shape = (len(families), len(PENSIONS), len(CLAIMS))
    g = {
        variable: np.asarray(simulation.calculate(variable, YEAR)).reshape(shape)
        for variable in BENUNIT_VARIABLES
    }
    for variable in PERSON_VARIABLES:
        values = simulation.calculate(variable, YEAR, map_to="benunit")
        g[variable] = np.asarray(values).reshape(shape)
    g["other_counted_benefits"] = sum(g[v] for v in OTHER_COUNTED_BENEFITS)
    # Council Tax Reduction income before the taxes deducted from it and apart
    # from the other benefits it counts.
    g["income_before_tax"] = (
        g["council_tax_reduction_applicable_income"]
        + g["income_tax"]
        + g["national_insurance"]
        - g["other_counted_benefits"]
    )
    # Cells whose Council Tax Reduction income follows the general rules, not
    # the Pension Credit routes of SSI 2012/319 regs 24 and 25.
    g["general_rules"] = ~(
        g["in_receipt_of_guarantee_credit"].astype(bool)
        | g["in_receipt_of_savings_credit_only"].astype(bool)
    )
    return g


def partial(g, i):
    """Where the award is neither nil nor the whole council tax bill."""
    award = g["council_tax_benefit"][i]
    return (award > 0.01) & (award < np.max(award) - 0.01)


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=3))
@example([SAVINGS_CREDIT_CARER])
def test_council_tax_reduction_income_counts_the_carer_support_payment_component(
    families,
):
    g = grid(families)
    income = g["council_tax_reduction_applicable_income"]
    award = g["council_tax_benefit"]
    for i, fam in enumerate(families):
        claimed, unclaimed = g["carer_support_payment"][i].T
        assert np.allclose(claimed, CARER_SUPPORT_PAYMENT, atol=0.01), fam
        assert np.all(unclaimed == 0), fam
        assert np.allclose(
            g["scottish_carer_supplement"][i, :, 0],
            SCOTTISH_CARER_SUPPLEMENT,
            atol=0.01,
        ), fam
        assert np.all(g["carers_allowance"][i] == 0), fam
        # Only where the zero floor on income does not bind in either run, and
        # both runs follow the general rules.
        general = g["general_rules"][i, :, 0] & g["general_rules"][i, :, 1]
        compared = (income[i, :, 0] > 0) & (income[i, :, 1] > 0) & general
        # At the top of the pension grid every family follows the general
        # rules with positive income, so the comparison is never empty.
        assert compared.any(), fam
        rise = g["income_before_tax"][i, :, 0] - g["income_before_tax"][i, :, 1]
        assert np.allclose(rise[compared], CARER_SUPPORT_PAYMENT, atol=0.05), (
            fam,
            rise[compared],
        )
        # Claiming never raises the reduction. A carer who qualifies by hours
        # has the carer premium either way; one who qualifies by the award
        # gains the premium with it, so only the hours case is compared.
        if fam["by_hours"]:
            assert np.all(award[i, :, 0] <= award[i, :, 1] + 0.01), fam
            both_partial = partial(g, i)[:, 0] & partial(g, i)[:, 1] & general
            fall = award[i, :, 1] - award[i, :, 0]
            income_rise = income[i, :, 0] - income[i, :, 1]
            assert np.allclose(
                fall[both_partial],
                WITHDRAWAL_RATE * income_rise[both_partial],
                atol=0.05,
            ), (fam, fall[both_partial], income_rise[both_partial])


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=3))
@example([SAVINGS_CREDIT_CARER])
def test_council_tax_reduction_income_ignores_the_scottish_carer_supplement(
    families,
):
    g = grid(families)
    without = grid(families, reform=NO_SCOTTISH_CARER_SUPPLEMENT)
    for i, fam in enumerate(families):
        # The carer claims in column 0.
        assert np.all(g["scottish_carer_supplement"][i, :, 0] > 0), fam
        assert np.all(without["scottish_carer_supplement"][i] == 0), fam
        for variable in ["carer_support_payment", "other_counted_benefits"]:
            assert np.allclose(g[variable][i], without[variable][i], atol=0.01), (
                fam,
                variable,
            )
        income = g["council_tax_reduction_applicable_income"][i]
        income_without = without["council_tax_reduction_applicable_income"][i]
        # Only where the zero floor on income does not bind in either run, and
        # both runs follow the general rules.
        general = g["general_rules"][i] & without["general_rules"][i]
        compared = (income > 0) & (income_without > 0) & general
        assert compared.any(), fam
        assert np.allclose(
            (income + g["income_tax"][i])[compared],
            (income_without + without["income_tax"][i])[compared],
            atol=0.05,
        ), fam
        award = g["council_tax_benefit"][i]
        award_without = without["council_tax_benefit"][i]
        # The supplement can only add tax, which lowers income.
        assert np.all(award >= award_without - 0.01), fam
        both_partial = partial(g, i) & partial(without, i) & general
        tax_on_supplement = g["income_tax"][i] - without["income_tax"][i]
        assert np.allclose(
            (award - award_without)[both_partial],
            WITHDRAWAL_RATE * tax_on_supplement[both_partial],
            atol=0.05,
        ), fam
        # Without a claim there is no supplement, so nothing moves.
        assert np.allclose(income[:, 1], income_without[:, 1], atol=0.01), fam
        # The supplement never lowers the award, even on the Pension Credit
        # routes; on them income follows invariant 4.


@PROPERTY_SETTINGS
@given(st.lists(family(countries=tuple(REGIONS)), min_size=1, max_size=3))
def test_council_tax_reduction_and_housing_benefit_assess_the_same_carer_income(
    families,
):
    g = grid(families)
    for i, fam in enumerate(families):
        carer_benefit = g["carers_allowance"][i] + g["carer_support_payment"][i]
        assert np.all(carer_benefit[:, 0] > 0), fam
        ctr_income = g["council_tax_reduction_applicable_income"][i]
        hb_income = g["housing_benefit_applicable_income"][i]
        # Guarantee Credit passports pension-age Housing Benefit to nil
        # income; the zero floors must not bind.
        passported = fam["pension_age"] & (g["guarantee_credit"][i] > 0)
        compared = (
            ~passported & g["general_rules"][i] & (hb_income > 0) & (ctr_income > 0)
        )
        assert compared.any(), fam
        hb_before_adjustments = (
            hb_income
            + g["housing_benefit_applicable_income_disregard"][i]
            + g["housing_benefit_applicable_income_childcare_element"][i]
            - g["housing_benefit_tariff_income"][i]
        )
        assert np.allclose(
            hb_before_adjustments[compared], ctr_income[compared], atol=0.05
        ), (fam, hb_before_adjustments[compared], ctr_income[compared])


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=3))
@example([SAVINGS_CREDIT_CARER])
def test_council_tax_reduction_income_on_the_pension_credit_routes(families):
    g = grid(families)
    for i, fam in enumerate(families):
        income = g["council_tax_reduction_applicable_income"][i]
        guarantee = g["in_receipt_of_guarantee_credit"][i].astype(bool)
        savings_only = g["in_receipt_of_savings_credit_only"][i].astype(bool)
        assert not np.any(guarantee & savings_only), fam
        assert np.all(income[guarantee] == 0), fam
        expected = g["pension_credit_income"][i] + g["pension_credit"][i]
        assert np.allclose(income[savings_only], expected[savings_only], atol=0.01), (
            fam,
            income[savings_only],
            expected[savings_only],
        )
