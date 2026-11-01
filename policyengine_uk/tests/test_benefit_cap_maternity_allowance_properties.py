"""DWP and councils count Maternity Allowance in the benefit cap.

Parliament lists maternity allowance among the welfare benefits whose total
the Secretary of State may cap by regulations (Welfare Reform Act 2012
s.96(1), (10)(i)), and the woman entitled to it receives it (Social Security
Contributions and Benefits Act 1992 s.35(1)). Under UC Regs 2013 regs 79(1)
and 80(1) and HB Regs 2006 reg 75A, DWP and councils count the welfare
benefits "to which the single person or couple is entitled". Under regs 80(4)
and 75C(4) they use the amount they count as income. DWP counts all of a Maternity Allowance as unearned income (UC Regs
2013 reg 66(1)(b)(viii)), and councils disregard none of it under HB Regs 2006
reg 40 and Schedule 5.

Invariants, for families on Universal Credit or on Housing Benefit alone,
whether a single claimant, either member of a couple, or a non-dependent
adult receives the allowance:

1. Exchange: moving an amount between the holder's Maternity Allowance and
   an equal amount of another welfare benefit of theirs that DWP or the
   council counts in the same way leaves the cap's total, both exemptions and
   both reductions unchanged. For Universal Credit the tests draw the other
   benefit from contribution-based JSA or ESA, incapacity benefit, severe
   disablement allowance and widowed parent's allowance. DWP counts JSA, ESA
   and widowed parent's allowance in full as unearned income (UC Regs 2013
   regs 66(1)(b)(i), (ii), (vi) and 80(4)), and the other two at the amount
   of the award (reg 80(1)). For Housing Benefit the tests draw
   contribution-based JSA or ESA, which councils count at the amount of the
   award (HB Regs 2006 reg 75C(1), (4)), or severe disablement allowance,
   which no paragraph of Schedule 5 disregards and which bears no income tax
   (ITEPA 2003 s.677(1)). Councils disregard £15 a week of widowed parent's
   allowance (Sch 5 para 16(b)) and any tax paid on incapacity benefit (Sch 5
   para 1; ITEPA 2003 s.660(1)), so the tests give families on Housing
   Benefit neither.
2. Coefficient one: with each award before the cap entered, so that
   Universal Credit does not taper, raising the holder's allowance by d
   raises the total by d for a claimant or partner, and leaves it unchanged
   for a non-dependent adult. The total therefore never falls as the
   allowance rises, and nor does either reduction.
3. Differential: the total equals a reference that follows s.96(10) and
   those regulations: the listed benefits of the claimant and partner, plus
   the family's Child Benefit, Child Tax Credit, Income Support, and
   Universal Credit and Housing Benefit before the cap. DWP reduces Universal
   Credit by the excess over the statutory limit (UC reg 80A(2)), counting
   Housing Benefit as nil (reg 80(2A)). Councils reduce Housing Benefit by the
   excess over theirs (HB reg 75CA(2)), leaving at least 50p a week (reg
   75D(2)).
4. Pound for pound, through the whole model: where the model works out
   Universal Credit and the award before the cap stays above nil, raising
   the mother's allowance by d lowers that award by d (reg 66(1)(b)(viii)),
   so the total does not move. Where DWP reduces the award at both
   amounts, and the award absorbs the whole reduction at each, Universal
   Credit after the cap plus the allowance does not move either: DWP holds
   the family's capped benefits at the limit whichever of them the allowance
   replaces. That needs an award large enough to take the whole excess and no
   protected floor that limits the reduction. Once the reduction takes the
   award to nil, DWP has nothing left to reduce, and each further pound of
   allowance adds a pound to what the family keeps.
   test_a_mother_of_16_keeps_more_allowance_once_dwp_cuts_her_award_to_nil
   checks that edge.

Each example fills fixed benefit units in one simulation per module, so the
draws set amounts while each family's members stay fixed.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
# Outside London, 2025-26 (UC Regs 2013 reg 80A(2)(c), (d); HB Regs 2006 reg
# 75CA(2)(c), (d)).
SINGLE_LIMIT, COUPLE_LIMIT = 14_753, 22_020
# HB Regs 2006 reg 75: councils pay no Housing Benefit of less than 50p a
# week.
HOUSING_BENEFIT_MINIMUM = 0.50 * 52

# The holder's other welfare benefits that DWP and councils count in the cap
# as theirs (WRA 2012 s.96(10)(d), (f), (h), (j), (n)), each entered as an
# award. Each scheme's list holds those that DWP or the council counts at the
# amount of the award, as each counts Maternity Allowance (invariant 1).
OTHER_BENEFITS = {
    "uc": [
        "jsa_contrib",
        "esa_contrib",
        "incapacity_benefit",
        "sda",
        "widowed_parents_allowance",
    ],
    "hb": ["jsa_contrib", "esa_contrib", "sda"],
}
FAMILY_AWARDS = ["child_benefit", "child_tax_credit", "income_support"]

# Families by structure: True for each member whose benefits DWP and councils
# count, the claimant or partner.
STRUCTURES = {
    "single": [True],
    "couple": [True, True],
    "non_dependant": [True, False],
}
# Who holds the moved allowance: a structure and a member of it.
HOLDERS = [
    ("single", 0),
    ("couple", 0),
    ("couple", 1),
    ("non_dependant", 0),
    ("non_dependant", 1),
]
SCHEMES = ["uc", "hb"]
VARIANTS = ["base", "allowance", "other", "split"]
ROWS = 3
# The benefit units of one row, in order.
UNITS = [
    (holder, scheme, variant)
    for holder in HOLDERS
    for scheme in SCHEMES
    for variant in VARIANTS
]


def entered_situation():
    people, benunits, households = {}, {}, {}
    for row in range(ROWS):
        for i, ((structure, _), scheme, variant) in enumerate(UNITS):
            unit = f"r{row}_u{i}"
            members = []
            for j, counted in enumerate(STRUCTURES[structure]):
                name = f"{unit}_p{j}"
                members.append(name)
                people[name] = {
                    "age": {YEAR: 40 - 2 * j},
                    "is_claimant_or_partner": {YEAR: counted},
                    "current_education": {YEAR: "NOT_IN_EDUCATION"},
                    # With no ESA support component, DWP and councils grant
                    # no exemption for contribution-based ESA (UC reg
                    # 83(1)(a); HB reg 75F(1)(a)).
                    "esa_includes_support_component": {YEAR: False},
                    "jsa_income_reported": {YEAR: 0},
                    "esa_income_reported": {YEAR: 0},
                }
            benunits[unit] = {
                "members": members,
                # The tests enter the LCWRA and carer elements as nil, so
                # neither exempts the family (UC reg 83(1)(a), (j)).
                "uc_LCWRA_element": {YEAR: 0},
                "uc_carer_element": {YEAR: 0},
            }
            if structure == "couple":
                benunits[unit]["relation_type"] = {YEAR: "COUPLE"}
            households[f"{unit}_home"] = {
                "members": members,
                "region": {YEAR: "NORTH_EAST"},
            }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def entered():
    return Simulation(situation=entered_situation())


PERSON_AMOUNTS = ["maternity_allowance_reported", *OTHER_BENEFITS["uc"]]
# The benefits each scheme's families receive. Families on Housing Benefit
# receive none of the others, which councils can count at less than the award.
SCHEME_AMOUNTS = {
    scheme: ["maternity_allowance_reported", *others]
    for scheme, others in OTHER_BENEFITS.items()
}
pounds = st.integers(0, 1_200_000).map(lambda pence: pence / 100)


@st.composite
def rows(draw):
    """One row's amounts: the amount moved and its split, the other benefit
    it moves to under each scheme, every member's own benefits before the
    move, and the family's awards."""
    moved = draw(pounds)
    split = round(moved * draw(st.integers(0, 100)) / 100, 2)
    return {
        "moved": moved,
        "split": split,
        "other": {
            scheme: draw(st.sampled_from(others))
            for scheme, others in OTHER_BENEFITS.items()
        },
        # Benefits before the move, for the first and second member.
        "own": [
            {
                name: draw(st.sampled_from([0.0, 0.0, 1_000.0]) | pounds)
                for name in PERSON_AMOUNTS
            }
            for _ in range(2)
        ],
        "family": {name: draw(st.integers(0, 4_000)) for name in FAMILY_AWARDS},
        "universal_credit": draw(st.integers(1, 35_000)),
        "housing_benefit": draw(st.integers(1, 25_000)),
    }


def holder_amounts(row, scheme, variant):
    """The holder's Maternity Allowance and other benefit after the move."""
    allowance = row["own"][0]["maternity_allowance_reported"]
    other = row["own"][0][row["other"][scheme]]
    added_to_allowance = {
        "base": 0,
        "allowance": row["moved"],
        "other": 0,
        "split": row["split"],
    }[variant]
    added_to_other = {
        "base": 0,
        "allowance": 0,
        "other": row["moved"],
        "split": row["moved"] - row["split"],
    }[variant]
    return allowance + added_to_allowance, other + added_to_other


def member_amounts(row, structure, holder, scheme, variant):
    """Each member's own benefits after the move, by member: the holder takes
    the first member's benefits before the move, any other member the
    second's, and a member receives nothing of a benefit outside the scheme's
    list."""
    members = []
    for j, _ in enumerate(STRUCTURES[structure]):
        own = dict(row["own"][0 if j == holder else 1])
        if j == holder:
            allowance, other = holder_amounts(row, scheme, variant)
            own["maternity_allowance_reported"] = allowance
            own[row["other"][scheme]] = other
        members.append(
            {
                name: own[name] if name in SCHEME_AMOUNTS[scheme] else 0.0
                for name in PERSON_AMOUNTS
            }
        )
    return members


def fill(sim, drawn):
    """Enter each row's amounts into the fixed families and recalculate."""
    person_inputs = {name: [] for name in PERSON_AMOUNTS}
    unit_inputs = {
        name: []
        for name in [
            *FAMILY_AWARDS,
            "universal_credit_pre_benefit_cap",
            "housing_benefit_pre_benefit_cap",
        ]
    }
    for row in drawn:
        for (structure, holder), scheme, variant in UNITS:
            for own in member_amounts(row, structure, holder, scheme, variant):
                for name in PERSON_AMOUNTS:
                    person_inputs[name].append(own[name])
            for name in FAMILY_AWARDS:
                unit_inputs[name].append(row["family"][name])
            unit_inputs["universal_credit_pre_benefit_cap"].append(
                row["universal_credit"] if scheme == "uc" else 0
            )
            unit_inputs["housing_benefit_pre_benefit_cap"].append(
                row["housing_benefit"] if scheme == "hb" else 0
            )
    for name, values in {**person_inputs, **unit_inputs}.items():
        sim.set_input(name, YEAR, np.array(values, dtype=float))
    sim.reset_calculations()


OUTPUTS = [
    "benefit_cap_welfare_benefits",
    "is_uc_benefit_cap_exempt",
    "is_housing_benefit_benefit_cap_exempt",
    "uc_benefit_cap",
    "housing_benefit_benefit_cap",
    "uc_benefit_cap_reduction",
    "housing_benefit_benefit_cap_reduction",
]


def results(sim, drawn):
    """Each output by row and unit: {name: array of shape (rows, units)}."""
    fill(sim, drawn)
    out = {}
    for name in OUTPUTS:
        values = np.asarray(sim.calculate(name, YEAR)).astype(float)
        out[name] = values.reshape(ROWS, len(UNITS))
    return out


def column(holder, scheme, variant):
    return UNITS.index((holder, scheme, variant))


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(abs(float(v)) for v in values)


def reference_total(row, structure, holder, scheme, variant):
    """WRA 2012 s.96(10); UC Regs 2013 regs 79(1), 80(1); HB Regs 2006 reg
    75A: the claimant's and partner's own welfare benefits and the family's
    awards. A non-dependent adult receives their benefits in their own right.
    Each scheme's families receive only the benefits DWP or the council counts
    at the amount of the award."""
    members = member_amounts(row, structure, holder, scheme, variant)
    total = 0.0
    for own, counted in zip(members, STRUCTURES[structure]):
        if counted:
            total += sum(own[name] for name in SCHEME_AMOUNTS[scheme])
    total += sum(row["family"].values())
    if scheme == "uc":
        return total + row["universal_credit"]
    return total + row["housing_benefit"]


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
DRAWS = st.lists(rows(), min_size=ROWS, max_size=ROWS)


@SETTINGS
@given(DRAWS)
def test_moving_income_between_maternity_allowance_and_another_counted_benefit(
    entered, drawn
):
    out = results(entered, drawn)
    for r, row in enumerate(drawn):
        for holder in HOLDERS:
            for scheme in SCHEMES:
                event(f"{scheme}: moved to {row['other'][scheme]}")
                columns = [column(holder, scheme, v) for v in VARIANTS[1:]]
                for name in OUTPUTS:
                    values = out[name][r, columns]
                    assert np.all(np.abs(values - values[0]) <= tolerance(*values)), (
                        name,
                        holder,
                        scheme,
                        row,
                        values,
                    )


@SETTINGS
@given(DRAWS)
def test_total_rises_by_the_couples_allowance_and_never_falls(entered, drawn):
    out = results(entered, drawn)
    for r, row in enumerate(drawn):
        for structure, holder in HOLDERS:
            counted = STRUCTURES[structure][holder]
            for scheme in SCHEMES:
                base = column((structure, holder), scheme, "base")
                raised = column((structure, holder), scheme, "allowance")
                total = out["benefit_cap_welfare_benefits"][r]
                rise = total[raised] - total[base]
                expected = row["moved"] if counted else 0
                assert abs(rise - expected) <= tolerance(total[base], total[raised]), (
                    structure,
                    holder,
                    scheme,
                    row,
                    rise,
                )
                for name in [
                    "uc_benefit_cap_reduction",
                    "housing_benefit_benefit_cap_reduction",
                ]:
                    before, after = out[name][r, base], out[name][r, raised]
                    assert after >= before - tolerance(before, after), (
                        name,
                        structure,
                        holder,
                        scheme,
                        row,
                    )


@SETTINGS
@given(DRAWS)
def test_total_and_reductions_match_the_regulations(entered, drawn):
    out = results(entered, drawn)
    for r, row in enumerate(drawn):
        for (structure, holder), scheme, variant in UNITS:
            i = column((structure, holder), scheme, variant)
            total = out["benefit_cap_welfare_benefits"][r, i]
            expected = reference_total(row, structure, holder, scheme, variant)
            context = (structure, holder, scheme, variant, row)
            assert abs(total - expected) <= tolerance(total, expected), context
            # DWP and councils grant no exemption for these benefits (UC Regs
            # 2013 reg 83; HB Regs 2006 regs 75E, 75F).
            limit = COUPLE_LIMIT if structure == "couple" else SINGLE_LIMIT
            if scheme == "uc":
                assert not out["is_uc_benefit_cap_exempt"][r, i], context
                assert out["uc_benefit_cap"][r, i] == limit, context
                # UC reg 81, with no childcare costs element and no Housing
                # Benefit to count as nil (reg 80(2A)).
                reduction = max(expected - limit, 0)
                actual = out["uc_benefit_cap_reduction"][r, i]
            else:
                assert not out["is_housing_benefit_benefit_cap_exempt"][r, i], context
                assert out["housing_benefit_benefit_cap"][r, i] == limit, context
                # HB reg 75D(2).
                reduction = min(
                    max(expected - limit, 0),
                    max(row["housing_benefit"] - HOUSING_BENEFIT_MINIMUM, 0),
                )
                actual = out["housing_benefit_benefit_cap_reduction"][r, i]
            event(f"{scheme} capped: {reduction > 0}")
            assert abs(actual - reduction) <= tolerance(expected, limit), context


# Invariant 4: the model works out Universal Credit, 2026-27, for families
# renting privately in Tyneside. The mother claims alone in a lone-parent
# family and jointly, as the second member, in a couple.
MODEL_YEAR = 2026
MODEL_FAMILIES = {
    "lone_parent_1": [30, 2],
    "lone_parent_3": [30, 1, 4, 7],
    "couple_2": [33, 30, 3, 6],
    "couple_3": [33, 30, 1, 5, 9],
}
MOTHER = {"lone_parent_1": 0, "lone_parent_3": 0, "couple_2": 1, "couple_3": 1}
POINTS = ["lower", "higher"]
MODEL_UNITS = [(family, point) for family in MODEL_FAMILIES for point in POINTS]


def model_situation():
    people, benunits, households = {}, {}, {}
    for i, (family, _) in enumerate(MODEL_UNITS):
        unit = f"m{i}"
        members = [f"{unit}_p{j}" for j in range(len(MODEL_FAMILIES[family]))]
        for name, age in zip(members, MODEL_FAMILIES[family]):
            people[name] = {"age": {MODEL_YEAR: age}}
        benunits[unit] = {"members": members}
        if family.startswith("couple"):
            benunits[unit]["relation_type"] = {MODEL_YEAR: "COUPLE"}
        households[f"{unit}_home"] = {
            "members": members,
            "region": {MODEL_YEAR: "NORTH_EAST"},
            "brma": {MODEL_YEAR: "TYNESIDE"},
            "tenure_type": {MODEL_YEAR: "RENT_PRIVATELY"},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def modelled():
    return Simulation(situation=model_situation())


@st.composite
def model_draws(draw):
    """Each family's rent, the mother's allowance and the rise in it."""
    return {
        family: {
            "rent": draw(st.integers(3_000, 24_000)),
            # Up to 39 weeks at the 2026-27 standard rate, 194.32 a week.
            "allowance": draw(st.integers(0, 7_578)),
            "rise": draw(st.integers(1, 3_000)),
        }
        for family in MODEL_FAMILIES
    }


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(model_draws())
def test_universal_credit_falls_by_the_allowance_inside_the_cap(modelled, drawn):
    allowance, rent = [], []
    for family, point in MODEL_UNITS:
        d = drawn[family]
        amount = d["allowance"] + (d["rise"] if point == "higher" else 0)
        for j in range(len(MODEL_FAMILIES[family])):
            allowance.append(amount if j == MOTHER[family] else 0)
        rent.append(d["rent"])
    modelled.set_input(
        "maternity_allowance_reported", MODEL_YEAR, np.array(allowance, float)
    )
    modelled.set_input("rent", MODEL_YEAR, np.array(rent, float))
    modelled.reset_calculations()
    value = {
        name: np.asarray(modelled.calculate(name, MODEL_YEAR)).astype(float)
        for name in [
            "universal_credit_pre_benefit_cap",
            "benefit_cap_welfare_benefits",
            "uc_benefit_cap_reduction",
            "uc_benefit_cap_reduction_after_floor",
            "universal_credit",
        ]
    }
    for f, family in enumerate(MODEL_FAMILIES):
        lower, higher = 2 * f, 2 * f + 1
        d = drawn[family]
        before = value["universal_credit_pre_benefit_cap"]
        if not (before[lower] > 0 and before[higher] > 0):
            event("award before the cap reaches nil")
            continue
        context = (family, d, {k: v[[lower, higher]] for k, v in value.items()})
        assert abs(before[lower] - before[higher] - d["rise"]) <= tolerance(
            before[lower], before[higher]
        ), context
        total = value["benefit_cap_welfare_benefits"]
        assert abs(total[higher] - total[lower]) <= tolerance(
            total[lower], total[higher]
        ), context
        reduction = value["uc_benefit_cap_reduction"]
        applied = value["uc_benefit_cap_reduction_after_floor"]
        capped = reduction[lower] > 0 and reduction[higher] > 0
        # The award takes the whole reduction at both amounts: it doesn't
        # reach nil first, and no protected floor limits the reduction.
        absorbed = all(
            abs(applied[i] - reduction[i]) <= tolerance(reduction[i])
            for i in (lower, higher)
        )
        event(f"capped at both amounts: {capped}; award absorbs it: {absorbed}")
        if capped and absorbed:
            paid = value["universal_credit"]
            kept_lower = paid[lower] + d["allowance"]
            kept_higher = paid[higher] + d["allowance"] + d["rise"]
            assert abs(kept_higher - kept_lower) <= tolerance(
                kept_lower, kept_higher
            ), context


# The edge of invariant 4. A mother of 40 with 16 children (aged 1 to 15, and
# another of 7) owns her home outright outside London and has no earnings,
# 2026-27. Parliament revoked UC Regs 2013 reg 24A, the two-child limit, from
# 6 April 2026 through the Universal Credit (Removal of Two Child Limit) Act
# 2026 s.1(3)(a). Monthly Universal Credit before her allowance (DWP, Benefit
# and pension rates 2026 to 2027):
#   standard allowance, single 25 or over                 424.90
#   child element, first child born before 6 April 2017   351.88
#   child element, 15 more children, 15 x 303.94         4,559.10
#   maximum amount                                       5,335.88, or 64,030.56
#     a year
# Child Benefit: (27.05 + 15 x 17.90) x 52 = 15,368.60 a year (Child Benefit
# (Rates) Regulations 2006 reg 2(1)). DWP applies the limit of 22,020 for a
# single claimant with a child (reg 80A(2)(d)(ii)).
EDGE_CHILD_AGES = [*range(1, 16), 7]
EDGE_ALLOWANCES = [6_000, 7_000]


def test_a_mother_of_16_keeps_more_allowance_once_dwp_cuts_her_award_to_nil():
    people, benunits, households = {}, {}, {}
    for i, amount in enumerate(EDGE_ALLOWANCES):
        mother = f"e{i}_mother"
        children = [f"e{i}_child{j}" for j in range(len(EDGE_CHILD_AGES))]
        people[mother] = {
            "age": {MODEL_YEAR: 40},
            "maternity_allowance_reported": {MODEL_YEAR: amount},
        }
        for child, age in zip(children, EDGE_CHILD_AGES):
            people[child] = {"age": {MODEL_YEAR: age}}
        benunits[f"e{i}"] = {"members": [mother, *children]}
        households[f"e{i}_home"] = {
            "members": [mother, *children],
            "region": {MODEL_YEAR: "NORTH_EAST"},
            "tenure_type": {MODEL_YEAR: "OWNED_OUTRIGHT"},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    value = {
        name: np.asarray(sim.calculate(name, MODEL_YEAR)).astype(float)
        for name in [
            "uc_maximum_amount",
            "child_benefit",
            "universal_credit_pre_benefit_cap",
            "benefit_cap_welfare_benefits",
            "uc_benefit_cap",
            "uc_benefit_cap_reduction",
            "uc_benefit_cap_reduction_after_floor",
            "universal_credit",
        ]
    }
    expected = {
        "uc_maximum_amount": [64_030.56, 64_030.56],
        "child_benefit": [15_368.60, 15_368.60],
        # Less the allowance in full (reg 66(1)(b)(viii)): both stay above nil.
        "universal_credit_pre_benefit_cap": [58_030.56, 57_030.56],
        # 58,030.56 + 15,368.60 + 6,000 = 57,030.56 + 15,368.60 + 7,000.
        "benefit_cap_welfare_benefits": [79_399.16, 79_399.16],
        "uc_benefit_cap": [22_020, 22_020],
        # Reg 81: 79,399.16 - 22,020 - 0 childcare = 57,379.16 at both amounts.
        "uc_benefit_cap_reduction": [57_379.16, 57_379.16],
        # At 7,000 DWP can take no more than the award before the cap,
        # 57,030.56.
        "uc_benefit_cap_reduction_after_floor": [57_379.16, 57_030.56],
        # 58,030.56 - 57,379.16 = 651.40, and nil.
        "universal_credit": [651.40, 0],
    }
    for name, amounts in expected.items():
        assert np.allclose(value[name], amounts, rtol=0, atol=0.01), (
            name,
            value[name],
        )
    # Universal Credit plus the allowance rises from 6,651.40 to 7,000: by
    # 348.60 of the 1,000 more allowance, the part the award could not absorb.
    kept = value["universal_credit"] + np.array(EDGE_ALLOWANCES)
    assert np.allclose(kept, [6_651.40, 7_000], rtol=0, atol=0.01), kept
