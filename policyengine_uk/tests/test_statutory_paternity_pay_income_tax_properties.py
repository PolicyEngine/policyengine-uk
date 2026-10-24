"""Property-based tests that income tax falls on statutory paternity pay.

ITEPA 2003 s. 660(1) Table A lists statutory paternity pay as a taxable UK
benefit, with statutory sick pay and statutory maternity pay. The model taxes
all three as employment income (employment_benefits, added to
taxable_employment_income) and charges Class 1 NI on all three
(ni_class_1_income). Housing Benefit and Council Tax Reduction count all three
as earnings (SI 2006/213 reg 35(1)(i); SI 2012/2885 Sch 1 para 18(1)(h) to
(j) and the equivalents) and deduct the tax on them.

Invariants, for any generated population of single people and couples, with
or without children, across the four UK nations, in which one adult receives
statutory paternity pay:

1. Monotonic: raising the recipient's statutory paternity pay, with
   everything else fixed, never lowers the recipient's income tax or the
   family's total income tax. A Child Benefit opt-out can lower the family's
   tax as income rises (the High Income Child Benefit Charge stops when the
   benefit stops), for wages too, so the generated families do not opt out.
2. Bounds: for families that do not claim Marriage Allowance, a pound more
   of statutory paternity pay raises the family's income tax before the
   winter fuel payment charge by at most a pound. Two cliffs are intended
   exceptions, and wages cross both the same way. Income Tax Act 2007
   s. 55B(2)(b) withdraws the whole Marriage Allowance reduction once the
   recipient is liable above the basic rate. ITEPA 2003 s. 681I charges back
   the whole winter fuel payment once the recipient's total income exceeds
   £35,000, so in income_tax one pound across that line costs the payment
   plus the tax on the pound (the last test below).
3. Same as statutory sick pay: statutory paternity pay of s gives every
   member the same income tax, National Insurance, adjusted net income and
   student loan repayment, and the family the same Housing Benefit and
   Council Tax Reduction income and Universal Credit, as statutory sick pay
   of s. Household net income is not compared: household_benefits counts
   statutory sick pay and not statutory paternity pay.
4. Same as wages: statutory paternity pay of s on top of wages of e gives the
   same income tax and National Insurance as wages of e + s, where the
   recipient's wages and trading profit cover their pension contributions.
   pension_contributions_relief caps relief at employment and self-employment
   income, which leaves statutory pay out, so a recipient whose contributions
   exceed those gets less relief on statutory pay than on wages.
5. Accounting: employment_benefits is statutory sick, maternity and
   paternity pay, and taxable_employment_income is wages plus those less
   employment deductions, floored at nil.

Every member's is_claimant_or_partner is set from its generated role, and
every attribute is set for every member: setting an input for anyone makes it
an input for everyone.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]
# Wages and payments on and around the 2026-27 thresholds: the personal
# allowance and primary threshold (12,570), the basic rate limit (50,270), the
# High Income Child Benefit Charge (60,000 to 80,000) and the personal
# allowance taper (100,000 to 125,140).
WAGES = [0, 0, 6_000, 12_570, 24_000, 50_000, 50_270, 62_000, 99_800, 126_000]
# Two weeks of statutory paternity pay at the 2026-27 rate is 388.64.
PAY = [0, 0, 1, 388.64, 2_000, 12_570, 30_000]
# Float32 amounts of tens of thousands of pounds are exact to about a penny.
TOLERANCE = 0.05

# The four versions of each family that a simulation holds: the recipient's
# statutory paternity pay at the lower and higher amount, the higher amount
# as statutory sick pay instead, and the higher amount as wages instead.
LOW, HIGH, AS_SICK_PAY, AS_WAGES = range(4)
VERSIONS = [LOW, HIGH, AS_SICK_PAY, AS_WAGES]

# Variables that statutory paternity pay and statutory sick pay of the same
# amount must leave the same (invariant 3).
PERSON_VARIABLES_AS_SICK_PAY = [
    "employment_benefits",
    "taxable_employment_income",
    "adjusted_net_income",
    "income_tax",
    "national_insurance",
    "student_loan_repayment",
]
FAMILY_VARIABLES_AS_SICK_PAY = [
    "housing_benefit_net_earnings",
    "housing_benefit_applicable_income",
    "council_tax_reduction_applicable_income",
    "uc_earned_income",
    "universal_credit",
]


@st.composite
def adults(draw, marriage_allowance):
    return dict(
        age=draw(st.sampled_from([24, 33, 45, 62, 70])),
        wages=float(draw(st.sampled_from(WAGES))),
        profit=float(draw(st.sampled_from([0, 0, 0, 9_000, 30_000, -4_000]))),
        pension_income=float(draw(st.sampled_from([0, 0, 6_000, 20_000]))),
        savings=float(draw(st.sampled_from([0, 0, 2_000, 15_000]))),
        dividends=float(draw(st.sampled_from([0, 0, 1_000, 20_000]))),
        pension_contributions=float(draw(st.sampled_from([0, 0, 2_000, 15_000]))),
        student_loan_plan=draw(st.sampled_from(["NONE", "NONE", "PLAN_2"])),
        claims_marriage_allowance=marriage_allowance and draw(st.booleans()),
    )


@st.composite
def families(draw, marriage_allowance=True):
    members = draw(st.lists(adults(marriage_allowance), min_size=1, max_size=2))
    amounts = st.one_of(st.sampled_from(PAY), st.integers(0, 40_000))
    low, high = sorted([draw(amounts), draw(amounts)])
    return dict(
        adults=members,
        married=len(members) == 2 and draw(st.booleans()),
        child_ages=draw(st.lists(st.sampled_from([0, 4, 11]), max_size=3)),
        region=draw(
            st.sampled_from(
                ["NORTH_EAST", "LONDON", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
            )
        ),
        tenure=draw(st.sampled_from(["RENT_FROM_COUNCIL", "RENT_PRIVATELY"])),
        rent=float(draw(st.sampled_from([0, 7_200, 18_000]))),
        would_claim_uc=draw(st.booleans()),
        recipient=draw(st.integers(0, len(members) - 1)),
        low=float(low),
        high=float(high),
    )


def populations(**kwargs):
    # Several families share one simulation, which costs little more than
    # one family does.
    return st.lists(families(**kwargs), min_size=4, max_size=10)


def member_inputs(family, index, version):
    """Inputs for one member of one version of a family."""
    is_adult = index < len(family["adults"])
    is_recipient = index == family["recipient"]
    paternity_pay = {LOW: family["low"], HIGH: family["high"]}.get(version, 0.0)
    sick_pay = family["high"] if version == AS_SICK_PAY else 0.0
    extra_wages = family["high"] if version == AS_WAGES else 0.0
    if is_adult:
        adult = family["adults"][index]
        inputs = {
            "age": adult["age"],
            "is_claimant_or_partner": True,
            "marital_status": "MARRIED" if family["married"] else "SINGLE",
            "employment_income": adult["wages"] + extra_wages * is_recipient,
            "self_employment_income": adult["profit"],
            "private_pension_income": adult["pension_income"],
            "savings_interest_income": adult["savings"],
            "dividend_income": adult["dividends"],
            "employee_pension_contributions": adult["pension_contributions"],
            "student_loan_plan": adult["student_loan_plan"],
            "would_claim_marriage_allowance": adult["claims_marriage_allowance"],
        }
    else:
        inputs = {
            "age": family["child_ages"][index - len(family["adults"])],
            "is_claimant_or_partner": False,
            "marital_status": "SINGLE",
            "employment_income": 0.0,
            "self_employment_income": 0.0,
            "private_pension_income": 0.0,
            "savings_interest_income": 0.0,
            "dividend_income": 0.0,
            "employee_pension_contributions": 0.0,
            "student_loan_plan": "NONE",
            "would_claim_marriage_allowance": False,
        }
    inputs["statutory_paternity_pay"] = paternity_pay * is_recipient
    inputs["statutory_sick_pay"] = sick_pay * is_recipient
    inputs["statutory_maternity_pay"] = 0.0
    return {name: {YEAR: value} for name, value in inputs.items()}


class Results:
    """One simulation holding every family once per version."""

    def __init__(self, population):
        people, benunits, households = {}, {}, {}
        self.first_member = {}
        for i, family in enumerate(population):
            size = len(family["adults"]) + len(family["child_ages"])
            for version in VERSIONS:
                self.first_member[i, version] = len(people)
                names = [f"person_{i}_{version}_{j}" for j in range(size)]
                for j, name in enumerate(names):
                    people[name] = member_inputs(family, j, version)
                benunits[f"benunit_{i}_{version}"] = {
                    "members": names,
                    "would_claim_uc": {YEAR: family["would_claim_uc"]},
                    "child_benefit_opts_out": {YEAR: False},
                }
                households[f"household_{i}_{version}"] = {
                    "members": names,
                    "region": {YEAR: family["region"]},
                    "tenure_type": {YEAR: family["tenure"]},
                    "rent": {YEAR: family["rent"]},
                }
        self.population = population
        self.people = len(people)
        self.simulation = Simulation(
            situation=dict(people=people, benunits=benunits, households=households)
        )
        self._cache = {}

    def _values(self, variable):
        if variable not in self._cache:
            self._cache[variable] = np.array(
                self.simulation.calculate(variable, YEAR), dtype=float
            )
        return self._cache[variable]

    def families(self, variable, version):
        """A benefit unit variable for one version of every family."""
        values = self._values(variable)
        return values.reshape(len(self.population), len(VERSIONS))[:, version]

    def members(self, variable, i, version):
        """A person variable for every member of one version of a family."""
        family = self.population[i]
        size = len(family["adults"]) + len(family["child_ages"])
        start = self.first_member[i, version]
        values = self._values(variable)
        assert values.size == self.people, f"{variable} is not a person variable"
        return values[start : start + size]

    def recipient(self, variable, i, version):
        return self.members(variable, i, version)[self.population[i]["recipient"]]

    def family_total(self, variable, i, version):
        return float(self.members(variable, i, version).sum())


def claims_marriage_allowance(family):
    return family["married"] and any(
        adult["claims_marriage_allowance"] for adult in family["adults"]
    )


@PROPERTY_SETTINGS
@given(population=populations())
def test_income_tax_never_falls_as_statutory_paternity_pay_rises(population):
    results = Results(population)
    for i, family in enumerate(population):
        # Invariant 1.
        recipient_gain = results.recipient("income_tax", i, HIGH) - results.recipient(
            "income_tax", i, LOW
        )
        assert recipient_gain >= -TOLERANCE, family
        family_gain = results.family_total(
            "income_tax", i, HIGH
        ) - results.family_total("income_tax", i, LOW)
        assert family_gain >= -TOLERANCE, family
        # Invariant 2.
        if not claims_marriage_allowance(family):
            gain_before_charge = results.family_total(
                "income_tax_before_winter_fuel_payment_charge", i, HIGH
            ) - results.family_total(
                "income_tax_before_winter_fuel_payment_charge", i, LOW
            )
            assert gain_before_charge <= family["high"] - family["low"] + TOLERANCE, (
                family
            )


@PROPERTY_SETTINGS
@given(population=populations())
def test_statutory_paternity_pay_is_treated_as_statutory_sick_pay(population):
    results = Results(population)
    for i, family in enumerate(population):
        # Invariant 3, for every member.
        for variable in PERSON_VARIABLES_AS_SICK_PAY:
            np.testing.assert_allclose(
                results.members(variable, i, HIGH),
                results.members(variable, i, AS_SICK_PAY),
                atol=TOLERANCE,
                err_msg=f"{variable}: {family}",
            )
    for variable in FAMILY_VARIABLES_AS_SICK_PAY:
        np.testing.assert_allclose(
            results.families(variable, HIGH),
            results.families(variable, AS_SICK_PAY),
            atol=TOLERANCE,
            err_msg=variable,
        )


def covers_pension_contributions(family):
    recipient = family["adults"][family["recipient"]]
    return (
        recipient["wages"] + recipient["profit"] >= recipient["pension_contributions"]
    )


@PROPERTY_SETTINGS
@given(population=populations())
def test_statutory_paternity_pay_is_taxed_as_wages(population):
    results = Results(population)
    for i, family in enumerate(population):
        if not covers_pension_contributions(family):
            continue
        # Invariant 4, for every member: the payment moves Marriage Allowance
        # and the High Income Child Benefit Charge as wages do.
        for variable in ["income_tax", "national_insurance", "adjusted_net_income"]:
            np.testing.assert_allclose(
                results.members(variable, i, HIGH),
                results.members(variable, i, AS_WAGES),
                atol=TOLERANCE,
                err_msg=f"{variable}: {family}",
            )


@PROPERTY_SETTINGS
@given(population=populations())
def test_statutory_pay_adds_up_to_taxable_employment_income(population):
    results = Results(population)
    for i, family in enumerate(population):
        for version in VERSIONS:
            # Invariant 5.
            statutory_pay = sum(
                results.members(variable, i, version) for variable in STATUTORY_PAY
            )
            np.testing.assert_allclose(
                results.members("employment_benefits", i, version),
                statutory_pay,
                atol=TOLERANCE,
                err_msg=str(family),
            )
            np.testing.assert_allclose(
                results.members("taxable_employment_income", i, version),
                np.maximum(
                    0,
                    results.members("employment_income", i, version)
                    + statutory_pay
                    - results.members("employment_deductions", i, version),
                ),
                atol=TOLERANCE,
                err_msg=str(family),
            )


def test_statutory_paternity_pay_on_the_basic_rate_bears_20_percent():
    # Two weeks of statutory paternity pay at the 2026-27 rate, £194.32 a
    # week (SI 2002/2818 reg 2(a)), on top of wages of £30,000 in England:
    # 20% of £388.64 is £77.728, as on the same amount of wages or sick pay.
    family = dict(
        adults=[
            dict(
                age=33,
                wages=30_000.0,
                profit=0.0,
                pension_income=0.0,
                savings=0.0,
                dividends=0.0,
                pension_contributions=0.0,
                student_loan_plan="NONE",
                claims_marriage_allowance=False,
            )
        ],
        married=False,
        child_ages=[0],
        region="NORTH_EAST",
        tenure="RENT_PRIVATELY",
        rent=0.0,
        would_claim_uc=False,
        recipient=0,
        low=0.0,
        high=388.64,
    )
    results = Results([family])
    tax = {v: results.recipient("income_tax", 0, v) for v in VERSIONS}
    assert abs(tax[LOW] - 0.2 * (30_000 - 12_570)) < 0.01
    assert abs(tax[HIGH] - tax[LOW] - 77.728) < 0.01
    assert abs(tax[AS_SICK_PAY] - tax[HIGH]) < 0.01
    assert abs(tax[AS_WAGES] - tax[HIGH]) < 0.01


def test_a_pound_of_statutory_paternity_pay_can_bring_the_winter_fuel_payment_charge():
    # A 70-year-old in England with £20,000 of private pension and £15,000 of
    # savings interest has total income of exactly £35,000, so the £200 Winter
    # Fuel Payment is not charged back. A pound of statutory paternity pay
    # takes total income over £35,000 (ITEPA 2003 s. 681I(1)(b)): income tax
    # rises by the whole payment plus 20% of the pound. Before the charge, the
    # pound costs only its 20p.
    family = dict(
        adults=[
            dict(
                age=70,
                wages=0.0,
                profit=0.0,
                pension_income=20_000.0,
                savings=15_000.0,
                dividends=0.0,
                pension_contributions=0.0,
                student_loan_plan="NONE",
                claims_marriage_allowance=False,
            )
        ],
        married=False,
        child_ages=[],
        region="NORTH_EAST",
        tenure="RENT_PRIVATELY",
        rent=0.0,
        would_claim_uc=False,
        recipient=0,
        low=0.0,
        high=1.0,
    )
    results = Results([family])

    def rise(variable):
        return results.recipient(variable, 0, HIGH) - results.recipient(
            variable, 0, LOW
        )

    assert results.recipient("winter_fuel_payment", 0, HIGH) == 200
    assert results.recipient("winter_fuel_payment_charge", 0, LOW) == 0
    assert results.recipient("winter_fuel_payment_charge", 0, HIGH) == 200
    assert abs(rise("income_tax_before_winter_fuel_payment_charge") - 0.2) < 0.01
    assert abs(rise("income_tax") - 200.2) < 0.01
