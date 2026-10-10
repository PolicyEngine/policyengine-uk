"""The Winter Fuel Payment and the Pension Age Winter Heating Payment follow
each person's own receipt of a relevant benefit.

Both schemes entitle and pay a person (SI 2000/729 reg 2; SI 2024/869 regs
2 to 4; SI 2025/969 regs 2 to 4; SSI 2024/351 regs 5, 9 and 10). Whether a
person is on a relevant benefit depends on the instrument:

- "paid to" the person (SI 2000/729, SI 2025/969): Income Support,
  income-based JSA, income-related ESA and Pension Credit are paid to one
  member of a couple, the one who reports the award or else the benefit-unit
  head (for Pension Credit, among the members who have attained the
  qualifying age, SPCA 2002 s.1(2)(b)). Universal Credit is awarded to the
  couple jointly and paid into an account the joint claimants nominate
  (Universal Credit etc. (Claims and Payments) Regulations 2013 reg 47(4);
  reg 47(6) pays it wholly to one member only by special arrangement), so it
  is paid to both. Tax credits count only under the 2024 instruments, which
  count the couple either way;
- through the couple (SI 2024/869 reg 2(5); SSI 2024/351 reg 7(2), 10(8) and
  2A): a member of a couple is on one when the other member is.

Either way a couple on one receives a single payment. Properties:

- the model matches a reference implementation written directly from the
  regulations, person by person, over households of up to three benefit
  units, in every country and in the 2023 to 2026 qualifying weeks;
- adding a non-dependant under pensionable age, with or without a relevant
  benefit of their own, never changes what anyone else is paid;
- from the 2025 qualifying week, a household of a single person or a couple
  (one benefit unit's claimant and partner, with no one else) receives the
  full amount for that unit
  (higher if anyone is 80 or over), whether or not they are on a relevant
  benefit: the shared amounts are halves (or, for two people over 80, a
  half of the higher amount each). The one exception is PAWHP from April
  2026, where two shared amounts of £105.55 make £211.10, 5p below £211.15.

Roles are given explicitly (is_claimant_or_partner) and the benefit-unit
awards are entered directly, so the properties test the winter payments
rather than role inference or the benefits' own means tests. Each example
builds many households in one simulation.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = [2023, 2024, 2025, 2026]
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Ages either side of pensionable age (66 to 67 over these years) and of 80.
PENSION_AGES = [67, 70, 79, 80, 85]
AGES = [40, 60, *PENSION_AGES]
INCOMES = [5_000, 20_000, 50_000]
AWARD = 1_000
# The benefit-unit award a couple can be on, and the input that carries it.
AWARD_INPUTS = {
    "PC": "pension_credit",
    "IS": "income_support",
    "JSA": "jsa_income",
    "ESA": "esa_income",
    "UC": "universal_credit",
    "TC": "tax_credits",
}
# The award a claimant reports themselves: the couple's payment is made to
# them (SI 2025/969 reg 4(2)(a); explanatory memorandum para 5.8).
REPORTED_INPUTS = {
    "PC": "pension_credit_reported",
    "IS": "income_support_reported",
    "JSA": "jsa_income_reported",
    "ESA": "esa_income_reported",
    "UC": "universal_credit_reported",
    "TC": "working_tax_credit_reported",
}
# An award reported by a member who is neither claimant nor partner. (An
# outside member's own income-related ESA or income-based JSA counts only if
# the award on their report is paid after the benefit unit's capital and
# eligibility screens, which the legacy award tests cover; the YAML tests
# cover the winter payments' side of it.)
OWN_AWARD_INPUTS = {
    "PC": "pension_credit_reported",
    "UC": "universal_credit_reported",
}
# Inputs for an award an outside member reports. The non-dependant property
# also draws income-related ESA: whether or not it is paid, it must never
# change anyone else's payment.
OWN_REPORT_INPUTS = {**OWN_AWARD_INPUTS, "ESA": "esa_income_reported"}
# Awards made to a couple jointly and paid to both: Universal Credit (WRA 2012
# s.1(2)(b); Claims and Payments Regulations 2013 reg 47(4) and (6)). Tax
# credits count only in the 2024 week, where the couple counts either way.
JOINT_AWARDS = {"UC", "TC"}

# Relevant benefits by scheme and qualifying week, as listed in the
# regulations (not read from the model's parameters).
WFP_RELEVANT = {
    # SI 2000/729 reg 2(1)(ii) and 3(1)(a)(i).
    2023: {"PC", "JSA", "ESA"},
    # SI 2024/869 reg 2(2)(b) and 2(4).
    2024: {"IS", "JSA", "PC", "ESA", "UC", "TC"},
    # SI 2025/969 reg 1(3).
    2025: {"IS", "JSA", "PC", "ESA", "UC"},
    2026: {"IS", "JSA", "PC", "ESA", "UC"},
}
PAWHP_RELEVANT = {
    # SSI 2024/351 reg 2 as made.
    2024: {"PC", "JSA", "ESA", "IS", "UC", "TC"},
    # Tax credits omitted by SSI 2025/195 reg 9(2).
    2025: {"PC", "JSA", "ESA", "IS", "UC"},
    2026: {"PC", "JSA", "ESA", "IS", "UC"},
}
# (lower, higher, shared under 80, 80+ sharing with under 80 only,
# 80+ sharing with another 80+).
WFP_AMOUNTS = (200, 300, 100, 200, 150)
PAWHP_AMOUNTS = {
    # SSI 2024/351 reg 10 as made: no shared amounts (only people on a
    # relevant benefit were entitled).
    2024: (200, 300, None, None, None),
    # SSI 2025/282 reg 9 (new reg 10); SSI 2025/100 reg 15.
    2025: (203.40, 305.10, 101.70, 203.40, 152.55),
    # SSI 2026/170 reg 15(3).
    2026: (211.15, 316.70, 105.55, 211.15, 158.35),
}
INCOME_LIMIT = 35_000


@st.composite
def benefit_units(draw):
    """A single person or a couple, with the award they are on, if any."""
    size = draw(st.integers(1, 2))
    adults = [
        {
            "age": draw(st.sampled_from(AGES)),
            "total_income": draw(st.sampled_from(INCOMES)),
        }
        for _ in range(size)
    ]
    award = draw(st.sampled_from([None, None, *AWARD_INPUTS]))
    # The benefit-unit head, and the member (if any) who reports the award.
    head = draw(st.integers(0, size - 1))
    reporter = draw(st.sampled_from([None, *range(size)])) if award else None
    return {"adults": adults, "award": award, "head": head, "reporter": reporter}


@st.composite
def other_members(draw):
    """A member of the first benefit unit who is neither claimant nor partner."""
    return {
        "age": draw(st.sampled_from(AGES)),
        "total_income": draw(st.sampled_from(INCOMES)),
        "own_award": draw(st.sampled_from([None, *OWN_AWARD_INPUTS])),
    }


@st.composite
def households(draw):
    return {
        "country": draw(st.sampled_from(COUNTRIES)),
        "units": draw(st.lists(benefit_units(), min_size=1, max_size=3)),
        "other": draw(st.one_of(st.none(), other_members())),
    }


def household_people(household):
    """Each person as (inputs, benefit unit index, claimant or partner).

    A claimant or partner's inputs carry whether they are the benefit-unit
    head and whether they report their unit's award.
    """
    people = []
    for u, unit in enumerate(household["units"]):
        for a, adult in enumerate(unit["adults"]):
            adult = {
                **adult,
                "head": a == unit.get("head", 0),
                "reports": a == unit.get("reporter"),
            }
            people.append((adult, u, True))
        if u == 0 and household["other"] is not None:
            people.append((household["other"], u, False))
    return people


def situation(drawn, year):
    people, benunits, hh = {}, {}, {}
    for h, household in enumerate(drawn):
        members = household_people(household)
        names = [f"h{h}_p{i}" for i in range(len(members))]
        for name, (inputs, _, cp) in zip(names, members):
            person = {
                "age": {year: inputs["age"]},
                "total_income": {year: inputs["total_income"]},
                "is_claimant_or_partner": {year: cp},
                "is_benunit_head": {year: bool(inputs.get("head", False))},
            }
            own = inputs.get("own_award")
            if own is not None:
                person[OWN_REPORT_INPUTS[own]] = {year: AWARD}
            people[name] = person
        for name, (inputs, u, cp) in zip(names, members):
            if cp and inputs.get("reports"):
                award = household["units"][u]["award"]
                people[name][REPORTED_INPUTS[award]] = {year: AWARD}
        for u, unit in enumerate(household["units"]):
            benunit = {
                "members": [n for n, m in zip(names, members) if m[1] == u],
                **{
                    variable: {year: AWARD if unit["award"] == key else 0}
                    for key, variable in AWARD_INPUTS.items()
                },
            }
            benunits[f"h{h}_b{u}"] = benunit
        hh[f"h{h}"] = {"members": names, "country": {year: household["country"]}}
    return {"people": people, "benunits": benunits, "households": hh}


def reference_payments(household, year):
    """WFP and PAWHP for each person, worked from the regulations.

    Everyone listed in AGES from 67 has reached pensionable age in these
    years and everyone under 67 has not.
    """
    country = household["country"]
    people = household_people(household)
    units = household["units"]

    def award_of(person):
        inputs, u, cp = person
        if cp:
            return units[u]["award"]
        return inputs.get("own_award")

    def is_payee(i):
        """Whether the couple's award is paid to this claimant or partner:
        the member who reports it, else the benefit-unit head. A Pension
        Credit claimant must have attained the qualifying age (SPCA 2002
        s.1(2)(b)), so where either member has, only such a member can be
        paid it: the reporter or head among them, else the only one."""
        u = people[i][1]
        couple = [j for j, q in enumerate(people) if q[1] == u and q[2]]
        if units[u]["award"] == "PC":
            able = [j for j in couple if people[j][0]["age"] >= 67]
            couple = able or couple
        if i not in couple:
            return False
        for role in ("reports", "head"):
            chosen = [j for j in couple if people[j][0][role]]
            if chosen:
                return i in chosen
        return i == max(couple, key=lambda j: (people[j][0]["age"], -j))

    def paid(relevant):
        """Whether a relevant benefit is paid to each person."""
        return [
            award_of(p) in relevant
            and (not p[2] or award_of(p) in JOINT_AWARDS or is_payee(i))
            for i, p in enumerate(people)
        ]

    def through_couple(receipt):
        """Each claimant or partner is on one when either of them is."""
        return [
            any(receipt[j] for j, q in enumerate(people) if q[1] == p[1] and q[2])
            if p[2]
            else receipt[i]
            for i, p in enumerate(people)
        ]

    def scheme(resident, relevant, means_test, amounts, partner_counts):
        lower, higher, shared, shared_80_with_under_80, shared_80_with_80 = amounts
        couple = through_couple(paid(relevant))
        on_relevant = couple if partner_counts else paid(relevant)
        qualifies = [resident and p[0]["age"] >= 67 for p in people]
        eligible = [q and (r or means_test) for q, r in zip(qualifies, on_relevant)]
        # One payment for a couple on a relevant benefit, to the claimant: the
        # member who reports the award, else the benefit-unit head, else the
        # elder (first listed if the same age). The other is not entitled.
        for u in range(len(units)):
            members = [
                i
                for i, p in enumerate(people)
                if p[1] == u and p[2] and qualifies[i] and couple[i]
            ]
            if members:
                payee = min(
                    members,
                    key=lambda i: (
                        0
                        if people[i][0]["reports"]
                        and units[people[i][1]]["award"] in relevant
                        else 1
                        if people[i][0]["head"]
                        else 2,
                        -people[i][0]["age"],
                        i,
                    ),
                )
                for i in members:
                    if i != payee:
                        eligible[i] = False
        payments = []
        for i, (inputs, u, cp) in enumerate(people):
            age = inputs["age"]
            if not eligible[i]:
                payments.append(0.0)
                continue
            if on_relevant[i]:
                partner_80 = cp and any(
                    q[1] == u and q[2] and q[0]["age"] >= 80 for q in people
                )
                payments.append(higher if age >= 80 or partner_80 else lower)
                continue
            others = [j for j in range(len(people)) if j != i and eligible[j]]
            others_80 = [j for j in others if people[j][0]["age"] >= 80]
            if age < 80:
                payments.append(shared if others else lower)
            elif others_80:
                payments.append(shared_80_with_80)
            elif others:
                payments.append(shared_80_with_under_80)
            else:
                payments.append(higher)
        return payments

    if year <= 2023:
        wfp_resident = True
        wfp_means = True
    else:
        wfp_resident = country in ("ENGLAND", "WALES", "NORTHERN_IRELAND")
        if year == 2024:
            wfp_means = False
        else:
            # The model's stand-in for the winter fuel payment charge.
            wfp_means = country in ("ENGLAND", "WALES") and any(
                p[0]["age"] >= 67 and p[0]["total_income"] < INCOME_LIMIT
                for p in people
            )
    # Only SI 2024/869 (reg 2(5)) counts the other member's benefit.
    wfp = scheme(wfp_resident, WFP_RELEVANT[year], wfp_means, WFP_AMOUNTS, year == 2024)
    if year >= 2024 and country == "SCOTLAND":
        pawhp = scheme(
            True, PAWHP_RELEVANT[year], year >= 2025, PAWHP_AMOUNTS[year], True
        )
    else:
        pawhp = [0.0] * len(people)
    return wfp, pawhp


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(st.sampled_from(YEARS), st.lists(households(), min_size=1, max_size=8))
def test_payments_match_reference(year, drawn):
    sim = Simulation(situation=situation(drawn, year))
    wfp = sim.calculate("winter_fuel_payment", year)
    pawhp = sim.calculate("pension_age_winter_heating_payment", year)
    wfa_household = sim.calculate("winter_fuel_allowance", year)
    pawhp_household = sim.calculate("pawhp", year)
    start = 0
    for h, household in enumerate(drawn):
        expected_wfp, expected_pawhp = reference_payments(household, year)
        n = len(expected_wfp)
        got_wfp = wfp[start : start + n]
        got_pawhp = pawhp[start : start + n]
        assert np.allclose(got_wfp, expected_wfp, atol=0.005), (
            year,
            household,
            got_wfp,
            expected_wfp,
        )
        assert np.allclose(got_pawhp, expected_pawhp, atol=0.005), (
            year,
            household,
            got_pawhp,
            expected_pawhp,
        )
        assert np.isclose(wfa_household[h], sum(expected_wfp), atol=0.01)
        assert np.isclose(pawhp_household[h], sum(expected_pawhp), atol=0.01)
        start += n


@st.composite
def non_dependants(draw):
    """An adult under pensionable age, in a benefit unit of their own or as a
    member of the first unit who is neither claimant nor partner, with or
    without a relevant benefit of their own."""
    return {
        "age": draw(st.sampled_from([19, 25, 40, 60])),
        "own_unit": draw(st.booleans()),
        "award": draw(st.sampled_from([None, "ESA", "PC", "UC"])),
    }


def with_non_dependant(household, non_dependant):
    """The household with the non-dependant added, and their position."""
    units = [dict(u) for u in household["units"]]
    other = household["other"]
    if non_dependant["own_unit"]:
        units.append(
            {
                "adults": [{"age": non_dependant["age"], "total_income": 0}],
                "award": non_dependant["award"],
            }
        )
        position = sum(len(u["adults"]) for u in household["units"])
    else:
        other = {
            "age": non_dependant["age"],
            "total_income": 0,
            "own_award": non_dependant["award"],
        }
        # Listed after the first unit's adults.
        position = len(household["units"][0]["adults"])
    added = {"country": household["country"], "units": units, "other": other}
    return added, position


@SETTINGS
@given(
    st.sampled_from(YEARS),
    st.lists(
        st.tuples(households().filter(lambda h: h["other"] is None), non_dependants()),
        min_size=1,
        max_size=6,
    ),
)
def test_non_dependants_never_change_anyone_elses_payment(year, drawn):
    without = [household for household, _ in drawn]
    added = [with_non_dependant(h, nd) for h, nd in drawn]
    with_nd = [household for household, _ in added]
    sim = Simulation(situation=situation(without + with_nd, year))
    sizes = [len(household_people(h)) for h in without + with_nd]
    starts = np.cumsum([0] + sizes[:-1])
    k = len(drawn)
    for variable in ["winter_fuel_payment", "pension_age_winter_heating_payment"]:
        values = sim.calculate(variable, year)
        for i in range(k):
            before = values[starts[i] : starts[i] + sizes[i]]
            after = values[starts[k + i] : starts[k + i] + sizes[k + i]]
            position = added[i][1]
            # The non-dependant is under pensionable age: never paid.
            assert after[position] == 0, (variable, year, drawn[i], after)
            # Everyone else is paid what they were paid without them.
            kept = np.delete(after, position)
            assert np.allclose(before, kept, atol=0.005), (
                variable,
                year,
                drawn[i],
                before,
                after,
            )


@st.composite
def one_unit_households(draw):
    """Every pension-age member in one benefit unit, under the income limit."""
    size = draw(st.integers(1, 2))
    adults = [
        {"age": draw(st.sampled_from([60, *PENSION_AGES])), "total_income": 5_000}
        for _ in range(size)
    ]
    if not any(a["age"] >= 67 for a in adults):
        adults[0]["age"] = draw(st.sampled_from(PENSION_AGES))
    return {
        "country": draw(st.sampled_from(["ENGLAND", "WALES", "SCOTLAND"])),
        "units": [
            {
                "adults": adults,
                "award": draw(st.sampled_from([None, "PC", "UC", "ESA"])),
            }
        ],
        "other": None,
    }


@SETTINGS
@given(
    st.sampled_from([2025, 2026]),
    st.lists(one_unit_households(), min_size=1, max_size=8),
)
def test_one_benefit_unit_receives_the_full_amount(year, drawn):
    sim = Simulation(situation=situation(drawn, year))
    wfa = sim.calculate("winter_fuel_allowance", year)
    pawhp = sim.calculate("pawhp", year)
    for h, household in enumerate(drawn):
        adults = household["units"][0]["adults"]
        any_80 = any(a["age"] >= 80 for a in adults)
        if household["country"] == "SCOTLAND":
            lower, higher, shared = PAWHP_AMOUNTS[year][:3]
            expected = higher if any_80 else lower
            pension_age = [a for a in adults if a["age"] >= 67]
            relevant = household["units"][0]["award"] is not None
            if not relevant and not any_80 and len(pension_age) == 2:
                # Two shared amounts: equal to the single amount in 2025,
                # 5p less from April 2026.
                expected = 2 * shared
            assert np.isclose(pawhp[h], expected, atol=0.005), (year, household)
            assert abs(pawhp[h] - (higher if any_80 else lower)) <= 0.05
            assert wfa[h] == 0
        else:
            assert wfa[h] == (300 if any_80 else 200), (year, household)
            assert pawhp[h] == 0
