"""Property-based tests that Universal Credit counts statutory pay as earnings.

Universal Credit Regulations 2013 reg. 55(4): statutory sick pay, statutory
maternity pay, statutory paternity pay, statutory adoption pay, statutory
shared parental pay, statutory parental bereavement pay and statutory neonatal
care pay "are to be treated as employed earnings". Reg. 55(5) takes relievable
pension contributions, income tax and primary Class 1 contributions off "the
amount of general earnings or benefits specified in paragraphs (2) to (4)".
The model has variables for the first three payments. It charges National
Insurance on all three (ni_class_1_income) and income tax on sick and maternity
pay (employment_benefits in taxable_employment_income), as it does on wages.

Before this was fixed the payments were left out of earned income while the
National Insurance on them, and the income tax on sick and maternity pay, were
still deducted, so the award rose by the taper rate times that tax as a
payment rose.

Invariants, for any generated population of single claimants and couples, with
or without children, in which one member receives one of the three payments:

1. Monotonic: raising a claimant's payment, with everything else fixed, never
   raises the award before the benefit cap. Three rules of law make
   exceptions, and none is a fault:

   a. Reg. 32(2)(b) treats a claimant receiving statutory sick, maternity or
      paternity pay as in paid work for the childcare costs element. So the
      first pound of a payment can open that element for a claimant with no
      other paid work. The award then rises by no more than the element does,
      and only as the payment starts from nil
      (test_first_pound_of_statutory_pay_can_open_the_childcare_element).
   b. Income Tax Act 2007 s. 55B(2)(b) withdraws the Marriage Allowance tax
      reduction in full once the recipient is liable at a rate the subsection
      does not list (it lists the basic rate and, for a Scottish taxpayer, the
      Scottish rates up to the intermediate rate). A pound of pay that crosses
      that line raises the tax on the earnings by more than a pound, earned
      income falls and the award rises. Wages do the same
      (test_marriage_allowance_cliff_is_the_same_as_for_wages), so the
      monotonic property is stated for families that do not claim Marriage
      Allowance.
   c. The benefit cap does not apply where earned income reaches the reg.
      82(1)(a) threshold, and the payments are earned income (reg. 55(4)). So
      a pound of pay can lift the cap and raise the final award. The award
      after the cap may therefore rise only where the family becomes exempt
      (is_benefit_cap_exempt); otherwise it obeys the same bound. The
      earnings exemption uses actual UC net earned income before the
      minimum income floor, which reg. 82(4) excludes.

2. Same as wages: statutory sick or maternity pay of s on top of wages of e
   gives the same income tax, National Insurance, earned income and award
   before and after the benefit cap as wages of e + s. This holds for Marriage Allowance
   claimants too. Two differences in the model's income tax are left out
   (counts_as_wages): it charges no income tax on statutory paternity pay, and
   it caps pension contribution relief at employment and self-employment
   income without statutory pay.

3. Accounting: a person's earned income before the minimum income floor is
   their wages, statutory pay and trading profit (a loss counts as nil) less
   their relievable pension contributions and the income tax and National
   Insurance on their earnings, floored at nil.

4. Bounds: a pound more of a payment adds between nothing and a pound to the
   recipient's earned income, for families that do not claim Marriage
   Allowance.

6. Household income: each payment counts once in household_benefits, and so
   in household net income. Raising it by d raises household_benefits by d
   plus the change in the other benefits listed there. Statutory paternity
   pay was in no household income list, so once Universal Credit tapered it
   household net income fell as the pay rose.

5. A dependant's payment changes neither the claimants' earned income nor the
   award (reg. 22(1)(b): "the claimant's earned income (or, in the case of
   joint claimants, their combined earned income)").

Every member's is_claimant_or_partner is set from its generated role, as the
FRS supplies it, and every attribute is set for every member: setting an
input for anyone makes it an input for everyone.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.gov.gov_spending import GOV_SPENDING_VARIABLES
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
)
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Reg. 55(4) payments the model has variables for.
PAYMENTS = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]
# The model charges income tax on these, as on wages (employment_benefits).
TAXED_AS_WAGES = ["statutory_sick_pay", "statutory_maternity_pay"]
BENEFITS = list(dict.fromkeys(HOUSEHOLD_BENEFIT_VARIABLES))
# Wages and payments on and around the 2026-27 thresholds: the personal
# allowance and primary threshold (12,570), the basic rate limit (50,270) and
# the personal allowance taper (100,000 to 125,140).
WAGES = [0, 0, 6_000, 12_570, 16_000, 24_000, 50_000, 50_270, 62_000, 100_000, 126_000]
PAY = [0, 0, 1, 300, 2_000, 6_000, 12_570, 20_000, 40_000]
# Float32 awards of tens of thousands of pounds are exact to about a penny.
TOLERANCE = 0.05

# The three versions of each family that a simulation holds.
LOW, HIGH, AS_WAGES = range(3)
VERSIONS = [LOW, HIGH, AS_WAGES]


@st.composite
def adults(draw, marriage_allowance):
    return dict(
        age=draw(st.sampled_from([22, 30, 45, 62, 68])),
        wages=float(draw(st.sampled_from(WAGES))),
        profit=float(draw(st.sampled_from([0, 0, 0, 9_000, 30_000, -4_000]))),
        startup=draw(st.booleans()),
        pension_contributions=float(draw(st.sampled_from([0, 0, 2_000]))),
        pension_income=float(draw(st.sampled_from([0, 0, 6_000]))),
        dividends=float(draw(st.sampled_from([0, 0, 4_000]))),
        lcwra=draw(st.booleans()),
        claims_marriage_allowance=marriage_allowance and draw(st.booleans()),
    )


@st.composite
def families(draw, marriage_allowance=False, dependant_recipient=False):
    members = draw(st.lists(adults(marriage_allowance), min_size=1, max_size=2))
    child_ages = draw(st.lists(st.sampled_from([1, 6, 13]), max_size=3))
    if dependant_recipient:
        # A qualifying young person: 17 and in non-advanced education.
        child_ages = [17] + child_ages[:2]
        recipient = len(members)
    else:
        recipient = draw(st.integers(0, len(members) - 1))
    amounts = st.one_of(st.sampled_from(PAY), st.integers(0, 40_000))
    low, high = sorted([draw(amounts), draw(amounts)])
    return dict(
        adults=members,
        child_ages=child_ages,
        childcare=float(draw(st.sampled_from([0, 0, 6_000]))),
        region=draw(
            st.sampled_from(
                ["NORTH_EAST", "LONDON", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
            )
        ),
        tenure=draw(st.sampled_from(["RENT_FROM_COUNCIL", "RENT_PRIVATELY"])),
        rent=float(draw(st.sampled_from([0, 7_200, 18_000, 36_000]))),
        recipient=recipient,
        payment=draw(st.sampled_from(PAYMENTS)),
        low=float(low),
        high=float(high),
    )


def populations(**kwargs):
    # Several families share one simulation, which costs little more than
    # one family does.
    return st.lists(families(**kwargs), min_size=4, max_size=10)


def member_inputs(family, index, version):
    """Inputs for one member of one version of a family.

    LOW and HIGH pay the recipient the lower and higher amount of the
    payment. AS_WAGES pays the higher amount as wages instead.
    """
    is_adult = index < len(family["adults"])
    is_recipient = index == family["recipient"]
    paid = {LOW: family["low"], HIGH: family["high"], AS_WAGES: 0.0}[version]
    extra_wages = family["high"] if is_recipient and version == AS_WAGES else 0.0
    if is_adult:
        adult = family["adults"][index]
        inputs = {
            "age": adult["age"],
            "is_claimant_or_partner": True,
            "employment_income": adult["wages"] + extra_wages,
            "self_employment_income": adult["profit"],
            "uc_is_in_startup_period": adult["startup"],
            "employee_pension_contributions": adult["pension_contributions"],
            "private_pension_income": adult["pension_income"],
            "dividend_income": adult["dividends"],
            "uc_limited_capability_for_WRA": adult["lcwra"],
            "would_claim_marriage_allowance": adult["claims_marriage_allowance"],
            "childcare_expenses": 0.0,
            "current_education": "NOT_IN_EDUCATION",
        }
    else:
        age = family["child_ages"][index - len(family["adults"])]
        inputs = {
            "age": age,
            "is_claimant_or_partner": False,
            "employment_income": extra_wages,
            "self_employment_income": 0.0,
            "uc_is_in_startup_period": False,
            "employee_pension_contributions": 0.0,
            "private_pension_income": 0.0,
            "dividend_income": 0.0,
            "uc_limited_capability_for_WRA": False,
            "would_claim_marriage_allowance": False,
            "childcare_expenses": family["childcare"] if age < 16 else 0.0,
            "current_education": "UPPER_SECONDARY" if age >= 16 else "PRIMARY",
        }
    for payment in PAYMENTS:
        inputs[payment] = paid if is_recipient and payment == family["payment"] else 0.0
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
                benunits[f"benunit_{i}_{version}"] = {"members": names}
                households[f"household_{i}_{version}"] = {
                    "members": names,
                    "region": {YEAR: family["region"]},
                    "tenure_type": {YEAR: family["tenure"]},
                    "rent": {YEAR: family["rent"]},
                }
        self.population = population
        self.simulation = Simulation(
            situation=dict(people=people, benunits=benunits, households=households)
        )

    def families(self, variable, version):
        """A benefit unit variable for one version of every family."""
        values = np.array(self.simulation.calculate(variable, YEAR), dtype=float)
        return values.reshape(len(self.population), len(VERSIONS))[:, version]

    def households(self, variable, version):
        """Any variable summed to the household, for one version of every family."""
        values = np.array(
            self.simulation.calculate(variable, YEAR, map_to="household"), dtype=float
        )
        return values.reshape(len(self.population), len(VERSIONS))[:, version]

    def person(self, variable, i, version, member):
        values = np.array(self.simulation.calculate(variable, YEAR), dtype=float)
        return values[self.first_member[i, version] + member]

    def recipient(self, variable, i, version):
        return self.person(variable, i, version, self.population[i]["recipient"])


# Release run 38366204407: explicit coverage is independent of Hypothesis's
# local source-constant pool, which differs for source and site-packages.
STATUTORY_SICK_PAY_CAP_REGRESSION = {
    "adults": [
        {
            "age": 22,
            "wages": 12_570.0,
            "profit": 0.0,
            "startup": False,
            "pension_contributions": 0.0,
            "pension_income": 6_000.0,
            "dividends": 0.0,
            "lcwra": False,
            "claims_marriage_allowance": False,
        }
    ],
    "child_ages": [1, 1],
    "childcare": 0.0,
    "region": "NORTH_EAST",
    "tenure": "RENT_FROM_COUNCIL",
    "rent": 0.0,
    "recipient": 0,
    "payment": "statutory_sick_pay",
    "low": 0.0,
    "high": 6_000.0,
}


def test_statutory_sick_pay_preserves_benefit_cap_earnings_exemption():
    """Reg. 55(4) pay cannot end this family's reg. 82(1)(a) exception."""
    results = Results([STATUTORY_SICK_PAY_CAP_REGRESSION])
    for version, expected_earnings in [(LOW, 12_570), (HIGH, 16_890)]:
        # The private pension absorbs the tax on unearned income. At HIGH,
        # actual earnings are 12,570 + 6,000 - 1,200 tax - 480 Class 1 NI.
        np.testing.assert_allclose(
            results.recipient("uc_individual_earned_income_before_mif", 0, version),
            expected_earnings,
            atol=TOLERANCE,
            rtol=0,
        )
        assert results.families("is_benefit_cap_exempt_earnings", version)[0]
        assert results.families("is_benefit_cap_exempt", version)[0]
        assert results.families("benefit_cap_reduction", version)[0] == 0
    assert (
        results.families("universal_credit", HIGH)[0]
        <= results.families("universal_credit", LOW)[0] + TOLERANCE
    )


@PROPERTY_SETTINGS
@example(population=[STATUTORY_SICK_PAY_CAP_REGRESSION])
@given(population=populations())
def test_award_never_rises_with_a_claimants_statutory_pay(population):
    results = Results(population)

    def both(variable):
        return {v: results.families(variable, v) for v in (LOW, HIGH)}

    before_cap = both("universal_credit_pre_benefit_cap")
    award = both("universal_credit")
    childcare = both("uc_childcare_element")
    exempt = both("is_benefit_cap_exempt")
    earned = "uc_individual_earned_income_before_mif"
    for i, family in enumerate(population):
        if family["low"] > 0:
            # The payment is already in payment, so reg. 32(2)(b) changes
            # nothing.
            assert childcare[HIGH][i] == childcare[LOW][i], family
        # Exception a: a payment that starts can open the childcare costs
        # element, and nothing else.
        opened = max(0, childcare[HIGH][i] - childcare[LOW][i])
        assert before_cap[HIGH][i] <= before_cap[LOW][i] + opened + TOLERANCE, family
        # Exception c: more earned income never ends an exemption from the
        # cap, and only a new exemption can raise the award after the cap.
        assert exempt[HIGH][i] >= exempt[LOW][i], family
        if exempt[HIGH][i] == exempt[LOW][i]:
            assert award[HIGH][i] <= award[LOW][i] + opened + TOLERANCE, family
        # Invariant 4: a pound more adds between nothing and a pound to the
        # recipient's earned income.
        gain = results.recipient(earned, i, HIGH) - results.recipient(earned, i, LOW)
        assert gain >= -TOLERANCE, family
        assert gain <= family["high"] - family["low"] + TOLERANCE, family
    # Invariant 6: each payment is in household_benefits once.
    for payment in PAYMENTS:
        rows = np.array([family["payment"] == payment for family in population])
        if not rows.any():
            continue

        def change(variable):
            return results.households(variable, HIGH) - results.households(
                variable, LOW
            )

        others = sum(change(benefit) for benefit in BENEFITS if benefit != payment)
        paid = np.array([family["high"] - family["low"] for family in population])
        np.testing.assert_allclose(
            (change("household_benefits") - others)[rows],
            paid[rows],
            atol=TOLERANCE,
            rtol=1e-5,
            err_msg=payment,
        )


def test_each_payment_is_household_income_and_government_spending():
    lists = {
        "HOUSEHOLD_BENEFIT_VARIABLES": HOUSEHOLD_BENEFIT_VARIABLES,
        "HBAI_HOUSEHOLD_NET_INCOME_ADDS": HBAI_HOUSEHOLD_NET_INCOME_ADDS,
        "hbai_benefits.adds": CountryTaxBenefitSystem().variables["hbai_benefits"].adds,
        "GOV_SPENDING_VARIABLES": GOV_SPENDING_VARIABLES,
    }
    for name, listed in lists.items():
        for payment in PAYMENTS:
            assert listed.count(payment) == 1, (name, payment)


def counts_as_wages(family):
    """Whether the model taxes the family's payment exactly as it taxes wages.

    It charges no income tax on statutory paternity pay. And
    pension_contributions_relief caps relief at employment and self-employment
    income, which leaves statutory pay out: a recipient whose wages and profit
    are below their pension contributions gets less relief on statutory pay
    than on the same amount of wages.
    """
    if family["recipient"] >= len(family["adults"]):
        return False
    recipient = family["adults"][family["recipient"]]
    covered = (
        recipient["wages"] + recipient["profit"] >= recipient["pension_contributions"]
    )
    return family["payment"] in TAXED_AS_WAGES and covered


@PROPERTY_SETTINGS
@given(population=populations(marriage_allowance=True))
def test_statutory_pay_counts_as_wages_and_earned_income_adds_up(population):
    results = Results(population)
    for i, family in enumerate(population):
        # Invariant 3, for every adult. No adult is 75 or over, the age from
        # which contributions stop being relievable.
        for member, adult in enumerate(family["adults"]):
            paid = family["high"] if member == family["recipient"] else 0.0
            gross = adult["wages"] + paid + max(0, adult["profit"])
            deductions = adult["pension_contributions"] + sum(
                results.person(variable, i, HIGH, member)
                for variable in [
                    "uc_income_tax_on_earnings",
                    "uc_national_insurance_on_earnings",
                ]
            )
            np.testing.assert_allclose(
                results.person(
                    "uc_individual_earned_income_before_mif", i, HIGH, member
                ),
                max(0, gross - deductions),
                atol=TOLERANCE,
                rtol=1e-6,
                err_msg=str(family),
            )
        # Invariant 2.
        if not counts_as_wages(family):
            continue
        for variable in [
            "income_tax",
            "national_insurance",
            "uc_income_tax_on_earnings",
            "uc_national_insurance_on_earnings",
            "uc_individual_earned_income_before_mif",
            "uc_individual_earned_income",
        ]:
            np.testing.assert_allclose(
                results.recipient(variable, i, HIGH),
                results.recipient(variable, i, AS_WAGES),
                atol=TOLERANCE,
                err_msg=f"{variable}: {family}",
            )
    for variable in [
        "uc_earned_income",
        "universal_credit_pre_benefit_cap",
        "is_benefit_cap_exempt_earnings",
        "universal_credit",
    ]:
        taxed = [counts_as_wages(family) for family in population]
        np.testing.assert_allclose(
            results.families(variable, HIGH)[taxed],
            results.families(variable, AS_WAGES)[taxed],
            atol=TOLERANCE,
            err_msg=variable,
        )


@PROPERTY_SETTINGS
@given(population=populations(marriage_allowance=True, dependant_recipient=True))
def test_a_dependants_statutory_pay_is_not_the_claimants_earned_income(population):
    results = Results(population)
    for variable in ["uc_earned_income", "universal_credit"]:
        np.testing.assert_array_equal(
            results.families(variable, HIGH),
            results.families(variable, LOW),
            err_msg=variable,
        )
    # The young person does have the earnings; they are just not the
    # claimants'.
    earned = "uc_individual_earned_income_before_mif"
    for i, family in enumerate(population):
        assert (
            results.recipient(earned, i, HIGH)
            >= results.recipient(earned, i, LOW) - TOLERANCE
        ), family


# Deterministic paths through the 2026-27 thresholds, for each payment.
PATH = [
    0,
    1,
    100,
    269,
    270,
    271,
    1_000,
    2_000,
    5_000,
    12_569,
    12_570,
    12_571,
    20_000,
    37_700,
    50_270,
    50_271,
    80_000,
]


def adult(age=30, wages=0.0, profit=0.0, claims_marriage_allowance=False):
    return dict(
        age=age,
        wages=wages,
        profit=profit,
        startup=False,
        pension_contributions=0.0,
        pension_income=0.0,
        dividends=0.0,
        lcwra=False,
        claims_marriage_allowance=claims_marriage_allowance,
    )


def family(adults, child_ages=(), rent=0.0, region="NORTH_EAST", childcare=0.0):
    return dict(
        adults=adults,
        child_ages=list(child_ages),
        childcare=childcare,
        region=region,
        tenure="RENT_FROM_COUNCIL",
        rent=rent,
        recipient=0,
    )


ARCHETYPES = {
    "single adult with no other income": family([adult()]),
    "lone parent on 20,000": family([adult(wages=20_000)], [5], rent=9_600),
    "couple on 50,000, crossing the basic rate limit": family(
        [adult(40, wages=50_000), adult(38)], [5, 5, 5], rent=36_000
    ),
    "couple on 99,000, crossing the personal allowance taper": family(
        [adult(40, wages=99_000), adult(38)], [5, 5, 5], rent=36_000
    ),
    "Scottish lone parent on 30,000": family(
        [adult(wages=30_000)], [5, 5], rent=18_000, region="SCOTLAND"
    ),
    "self-employed below the minimum income floor": family(
        [adult(profit=5_000)], rent=9_600
    ),
}


def along_paths(bases, payments, variables):
    """Each variable along PATH, for each base family and payment.

    Returns {variable: {version: array[base, payment, step]}}, where HIGH
    raises the payment along the path and AS_WAGES raises wages instead.
    """
    population = [
        dict(base, payment=payment, low=0.0, high=float(step))
        for base in bases
        for payment in payments
        for step in PATH
    ]
    results = Results(population)
    shape = (len(bases), len(payments), len(PATH))
    return {
        variable: {
            version: results.families(variable, version).reshape(shape)
            for version in (HIGH, AS_WAGES)
        }
        for variable in variables
    }


def test_award_falls_along_a_path_of_rising_statutory_pay():
    variables = [
        "universal_credit_pre_benefit_cap",
        "universal_credit",
        "is_benefit_cap_exempt",
    ]
    paths = along_paths(list(ARCHETYPES.values()), PAYMENTS, variables)
    for i, name in enumerate(ARCHETYPES):
        for j, payment in enumerate(PAYMENTS):
            path = paths["universal_credit_pre_benefit_cap"][HIGH][i, j]
            assert path[0] > 0, name
            assert (np.diff(path) <= TOLERANCE).all(), (name, payment, path)
            # The path takes the award down, so the test can fail.
            assert path[-1] < path[0] - 1_000, (name, payment, path)
            # After the cap, the award rises only at a step that makes the
            # family exempt (reg. 82(1)(a)).
            final = paths["universal_credit"][HIGH][i, j]
            newly_exempt = np.diff(paths["is_benefit_cap_exempt"][HIGH][i, j]) > 0
            rises = np.diff(final) > TOLERANCE
            assert not (rises & ~newly_exempt).any(), (name, payment, final)


def test_first_pound_of_statutory_pay_can_open_the_childcare_element():
    # Intended: reg. 32(2)(b) treats a claimant receiving statutory sick,
    # maternity or paternity pay as in paid work, which the childcare costs
    # element requires (reg. 32(1)(a)). The family has no rent, so the
    # benefit cap does not take any of the element back.
    base = family([adult()], [5], childcare=6_000)
    paths = along_paths([base], PAYMENTS, ["universal_credit", "uc_childcare_element"])
    for j, payment in enumerate(PAYMENTS):
        awards = paths["universal_credit"][HIGH][0, j]
        childcare = paths["uc_childcare_element"][HIGH][0, j]
        assert childcare[0] == 0
        assert childcare[1] > 0
        # The award rises by the element, less at most the pound of pay.
        rise = awards[1] - awards[0]
        assert childcare[1] - 1 - TOLERANCE <= rise <= childcare[1] + TOLERANCE
        # Once the payment is in payment the element does not move, and the
        # award never rises again.
        assert (childcare[1:] == childcare[1]).all()
        assert (np.diff(awards[1:]) <= TOLERANCE).all(), (payment, awards)


def test_marriage_allowance_cliff_is_the_same_as_for_wages():
    # Intended: ITA 2007 s. 55B(2)(b) withdraws the whole Marriage Allowance
    # reduction once the recipient (an English taxpayer here) is liable above
    # the basic rate. The pound of pay that takes the recipient past the
    # basic rate limit therefore lowers earned income and raises the award,
    # exactly as a pound of wages does. The monotonic property above leaves
    # these families out.
    base = family(
        [
            adult(40, wages=50_000, claims_marriage_allowance=True),
            adult(38, claims_marriage_allowance=True),
        ],
        [5, 5, 5],
        rent=36_000,
    )
    variables = ["uc_earned_income", "universal_credit_pre_benefit_cap"]
    paths = along_paths([base], TAXED_AS_WAGES, variables)
    for variable in variables:
        np.testing.assert_allclose(
            paths[variable][HIGH],
            paths[variable][AS_WAGES],
            atol=TOLERANCE,
            err_msg=variable,
        )
    # The cliff is there: the reduction goes in one step, and at that step
    # earned income falls and the award rises.
    population = [
        dict(base, payment=payment, low=0.0, high=float(step))
        for payment in TAXED_AS_WAGES
        for step in PATH
    ]
    results = Results(population)
    shape = (len(TAXED_AS_WAGES), len(PATH))
    reduction = np.array(
        [
            results.recipient("marriage_allowance", i, HIGH)
            for i in range(len(population))
        ]
    ).reshape(shape)
    for j, payment in enumerate(TAXED_AS_WAGES):
        assert reduction[j, 0] > 0 and reduction[j, -1] == 0, (payment, reduction[j])
        steps = np.flatnonzero(np.diff(reduction[j]) < 0)
        assert len(steps) == 1, (payment, reduction[j])
        step = steps[0]
        earned = paths["uc_earned_income"][HIGH][0, j]
        award = paths["universal_credit_pre_benefit_cap"][HIGH][0, j]
        assert earned[step + 1] < earned[step], (payment, earned)
        assert award[step + 1] > award[step], (payment, award)
