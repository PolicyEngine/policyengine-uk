"""Property-based tests for non-dependants within a benefit unit.

A benefit unit can include members aged 16 or over who are neither the
claimant or partner nor a qualifying young person: in law they are
non-dependants of the renter (UC Regs 2013 Sch 4 para 9; HB Regs 2006 reg 3;
CTR SI 2012/2885 reg 9 and equivalents). Invariants, for any generated
population of households:

1. Oracle: each family's Universal Credit, Housing Benefit and Council Tax
   Reduction non-dependant deductions, and who is eligible for an individual
   deduction, equal an independent calculation from the generated household
   structure: who is a non-dependant, of whom, how a non-dependant couple
   pays one deduction (the higher), and how a non-dependant of several joint
   occupiers is apportioned (by rent or liability share, whichever family
   the non-dependant is in).
2. Conservation: every Housing Benefit non-dependant deduction (a couple's
   counted once) is borne in full across the joint occupiers, and once more
   by a boarder or lodger for a non-dependant in its own benefit unit,
   unless a claimant is exempt; each Council Tax Reduction claiming family
   bears every non-dependant, under its own scheme, in proportion to its
   joint-liability share
   unless the applicant is exempt; every Universal Credit contribution is
   borne by exactly one family unless that family's renter is exempt.
3. Exemptions: a family whose renter is exempt (UC Sch 4 para 15; HB reg
   74(6); CTR Sch 1 para 8(6)) has no deductions; no deduction is charged for
   a non-dependant under 21 (UC) or under 18 (HB, CTR), or for a qualifying
   young person.
4. No-op: in households without non-dependants inside a benefit unit, the
   deductions equal the previous formulas, which charged only members of
   other families.
5. Local schemes: in Merton, Kingston upon Thames, Newham, Westminster and
   Oxford, each non-dependant's deduction and each claiming family's total
   equal an independent calculation from the council's scale: a claimant or
   partner banded on the couple's joint earnings and the couple deducted once
   at the higher amount (each member in Merton and Kingston upon Thames
   when the couple has Universal Credit), any other adult banded
   on their own earnings, each on their own hours; the benefit-receipt
   exemptions for the person on the award, Universal Credit's tested on their
   own earnings (none in Oxford); and the household's pool charged to each
   claiming family by its share, less its own applicant, partner and
   children, unless the applicant is exempt. Every other council's variables
   are zero. Conservation: the claiming families together bear the pool
   times the sum of their shares, which is the whole pool wherever the
   shares sum to one (they follow the regulations' per-person wording, so a
   couple jointly liable with others leaves its partner's share unborne).
6. Local independence: an adult in a benefit unit who is not its claimant or
   partner changes no one else's local deduction through their earnings.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period as make_period

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._national_non_dependants import (
    household_head_family_is_pensioner,
    individual_non_dep_deduction,
)

# Situation inputs without a period key are set for 2025, so the properties
# are checked in 2025, when the contribution was £93.02 a month.
YEAR = 2025
UC_CONTRIBUTION = 93.02 * 12
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Members of a benefit unit who are not the claimant or partner.
#   dependant: a qualifying young person the claimant is responsible for;
#   looked_after: a qualifying young person placed by a local authority, for
#     whom no one in the family is responsible;
#   non_dependant: aged 16 or over and not a qualifying young person.
KINDS = ["dependant", "looked_after", "non_dependant"]
ROLES = ["sharer", "lodger", "non_dependant"]


@st.composite
def extra_member(draw):
    kind = draw(st.sampled_from(KINDS))
    age = draw(st.integers(16, 19) if kind != "non_dependant" else st.integers(16, 60))
    return dict(
        kind=kind,
        age=age,
        earnings=draw(st.sampled_from([0, 2_600, 15_600, 30_000])),
        hours=draw(st.sampled_from([0, 10, 37.5])),
        attendance_allowance=draw(st.booleans()),
    )


@st.composite
def family(draw, role):
    # The household head's family has the household's oldest members, so it
    # is unambiguously the head's (and the council tax claimant's) family.
    adult_age = st.integers(61, 90) if role == "head" else st.integers(25, 59)
    return dict(
        role=role,
        adult_ages=draw(st.lists(adult_age, min_size=1, max_size=2)),
        extras=draw(st.lists(extra_member(), min_size=0, max_size=2)),
        child=draw(st.booleans()),
        renter_pip=draw(st.booleans()),
        # Take-up: a family flagged not to claim Universal Credit passes its
        # in-unit non-dependants to the claim that counts the household's.
        would_claim_uc=draw(st.booleans()),
        payment=draw(st.floats(1_000, 10_000, allow_nan=False)),
    )


@st.composite
def household(draw):
    head = draw(family("head"))
    others = [
        draw(family(draw(st.sampled_from(ROLES))))
        for _ in range(draw(st.integers(0, 2)))
    ]
    return dict(
        families=[head] + others,
        rent=draw(st.floats(3_000, 20_000, allow_nan=False)),
        tenure=draw(st.sampled_from(["RENT_FROM_COUNCIL", "RENT_PRIVATELY"])),
    )


population = st.lists(household(), min_size=1, max_size=5)


def build(population, convert=None):
    """One situation for the whole population, and a record per person and
    per family for the oracle. convert maps extra members' kinds to others."""
    people, benunits, homes = {}, {}, {}
    person_rows, family_rows = [], []
    for h, house in enumerate(population):
        members = []
        for f, fam in enumerate(house["families"]):
            name = f"h{h}_f{f}"
            ids = []
            head_family = f == 0
            # The head's family has the household's oldest member.
            for i, age in enumerate(fam["adult_ages"]):
                pid = f"{name}_adult_{i}"
                pip = fam["renter_pip"] and i == 0
                people[pid] = {
                    "age": age,
                    "is_claimant_or_partner": True,
                    "is_household_head": head_family and i == 0,
                    "pip_dl": 3_000.0 if pip else 0.0,
                }
                ids.append(pid)
                person_rows.append(
                    dict(
                        household=h,
                        family=len(family_rows),
                        kind="adult",
                        age=age,
                        disability_benefit=pip,
                    )
                )
            for i, extra in enumerate(fam["extras"]):
                kind = (convert or {}).get(extra["kind"], extra["kind"])
                pid = f"{name}_extra_{i}"
                young = kind != "non_dependant"
                people[pid] = {
                    "age": min(extra["age"], 19) if young else extra["age"],
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                    "is_qualifying_young_person_for_universal_credit": young,
                    "is_child_or_qualifying_young_person_for_child_benefit": young,
                    "is_looked_after_by_local_authority": kind == "looked_after",
                    "employment_income": float(extra["earnings"]),
                    "weekly_hours": float(extra["hours"]),
                    "attendance_allowance": (
                        3_000.0 if extra["attendance_allowance"] else 0.0
                    ),
                }
                ids.append(pid)
                person_rows.append(
                    dict(
                        household=h,
                        family=len(family_rows),
                        kind=kind,
                        age=people[pid]["age"],
                        disability_benefit=extra["attendance_allowance"],
                    )
                )
            if fam["child"]:
                pid = f"{name}_child"
                # Inputs set for some members are inputs for all, so the
                # child's Child Benefit status is stated, not left to default.
                people[pid] = {
                    "age": 8,
                    "is_claimant_or_partner": False,
                    "is_household_head": False,
                    "is_child_or_qualifying_young_person_for_child_benefit": True,
                }
                ids.append(pid)
                person_rows.append(
                    dict(
                        household=h,
                        family=len(family_rows),
                        kind="child",
                        age=8,
                        disability_benefit=False,
                    )
                )
            benunit = {"members": ids, "would_claim_uc": fam["would_claim_uc"]}
            if fam["role"] == "sharer":
                benunit["liable_for_share_of_household_rent"] = True
            if fam["role"] == "lodger":
                people[ids[0]]["rent_paid_as_lodger"] = fam["payment"]
            benunits[name] = benunit
            members.extend(ids)
            family_rows.append(
                dict(
                    household=h,
                    role=fam["role"],
                    renter_pip=fam["renter_pip"],
                    n_liable=len(fam["adult_ages"]),
                )
            )
        homes[f"h{h}"] = {
            "members": members,
            "rent": house["rent"],
            "tenure_type": house["tenure"],
            "brma": "MAIDSTONE",
        }
    situation = {"people": people, "benunits": benunits, "households": homes}
    return situation, person_rows, family_rows


def calc(sim, variable, map_to=None):
    return np.asarray(sim.calculate(variable, YEAR, map_to=map_to), dtype=float)


def counted_once_per_couple(person_rows, amounts):
    """A couple pays one deduction, the higher (HB reg 74(3); CTR Sch 1 para
    8(3)): keep the larger amount of each family's adults (its claimant and
    partner) and zero the other; anyone else counts in full."""
    counted = np.array(amounts, dtype=float)
    adults = {}
    for p, row in enumerate(person_rows):
        if row["kind"] == "adult":
            adults.setdefault(row["family"], []).append(p)
    for members in adults.values():
        keep = max(members, key=lambda p: (counted[p], -p))
        for p in members:
            if p != keep:
                counted[p] = 0.0
    return counted


def oracle(
    person_rows,
    family_rows,
    uc,
    hb,
    ctr,
    pension_credit,
    claims,
    ctr_share,
    uc_counted,
    uc_own_claim,
    ctr_other,
    ctr_own_scheme_is_heads,
):
    """Expected deductions per family from the generated structure.

    uc, hb and ctr are each person's individual deduction from the model;
    the oracle decides independently who is whose non-dependant. Which
    Universal Credit claim counts the household's non-dependants
    (uc_non_dependants_counted), whether a family makes its own claim, the
    CTR claim flags and the joint-liability shares are read from the model.
    ctr is each person's deduction under the scheme of the household head's
    family; ctr_other under the other scheme, which a claiming family on that
    scheme bears (SI 2012/2885 reg 3).
    """
    n = len(family_rows)
    exp_uc, exp_hb, exp_ctr = np.zeros(n), np.zeros(n), np.zeros(n)
    expected_uc_individual = np.zeros(len(person_rows))
    hb = counted_once_per_couple(person_rows, hb)
    ctr = counted_once_per_couple(person_rows, ctr)
    ctr_other = counted_once_per_couple(person_rows, ctr_other)
    households = sorted({f["household"] for f in family_rows})
    for h in households:
        fams = [i for i, f in enumerate(family_rows) if f["household"] == h]
        # Sch 4 para 9(2)(f): one claim counts the household's non-dependants.
        counted = [i for i in fams if uc_counted[i]]
        counted_family = counted[0] if counted else None
        # Families liable for the household's rent: the head's and sharers'.
        liable = [i for i in fams if family_rows[i]["role"] in ("head", "sharer")]
        total_liable = sum(family_rows[i]["n_liable"] for i in liable)
        share = {
            i: (family_rows[i]["n_liable"] / total_liable if i in liable else 0.0)
            for i in fams
        }
        for p, row in enumerate(person_rows):
            if row["household"] != h:
                continue
            f = row["family"]
            role = family_rows[f]["role"]
            other_family = role == "non_dependant"
            own_family = row["kind"] == "non_dependant"
            # UC: a member of a family not liable for rent counts in the
            # claim that counts the household's non-dependants; a non-QYP
            # member aged 16+ of any other family counts in their own family's
            # claim if it makes one, otherwise in that same counted claim.
            # Para 16: Attendance Allowance or PIP daily living, or Pension
            # Credit, which only a claimant or partner receives.
            uc_exempt = row["disability_benefit"] or (
                row["kind"] == "adult" and pension_credit[f] > 0
            )
            uc_non_dependant = other_family or own_family
            if uc_non_dependant and row["age"] >= 21 and not uc_exempt:
                expected_uc_individual[p] = UC_CONTRIBUTION
            own_claim = own_family and not other_family and uc_own_claim[f]
            bearer = f if own_claim else counted_family
            if (
                uc_non_dependant
                and bearer is not None
                and not family_rows[bearer]["renter_pip"]
            ):
                exp_uc[bearer] += uc[p]
            # HB: every non-dependant, in any family, is pooled across the
            # joint occupiers by rent share; a boarder or lodger, who is not
            # a joint occupier, also bears its own in full.
            if other_family or own_family:
                for i in fams:
                    exp_hb[i] += share[i] * hb[p]
                if own_family and role == "lodger":
                    exp_hb[f] += hb[p]
            # CTR: every non-dependant, a lodger's included, is pooled across
            # the claiming families by joint-liability share, except that a
            # family's own claimant or partner is not its non-dependant.
            if other_family or own_family:
                for i in fams:
                    if i == f and not own_family:
                        continue
                    amount = ctr[p] if ctr_own_scheme_is_heads[i] else ctr_other[p]
                    exp_ctr[i] += claims[i] * ctr_share[i] * amount
        # A claimant or partner on PIP daily living exempts their own family
        # from all HB and CTR deductions (reg 74(6); Sch 1 para 8(6)).
        for i in fams:
            if family_rows[i]["renter_pip"]:
                exp_hb[i] = 0.0
                exp_ctr[i] = 0.0
    return exp_uc, exp_hb, exp_ctr, expected_uc_individual


def ctr_by_scheme(sim, person_rows, family_rows):
    """Each person's CTR deduction under the other scheme (pensioner or
    working-age) from the household head's family, and whether each family is
    on the head's scheme. Computed with the aggregator's own helper, since a
    jointly liable applicant on the other scheme has its deductions
    recomputed under that scheme."""
    person = sim.populations["person"]
    period = make_period(YEAR)
    head_pensioner = np.asarray(household_head_family_is_pensioner(person, period))
    eligible = (
        calc(sim, "council_tax_reduction_individual_non_dep_deduction_eligible") > 0
    )
    other = np.asarray(
        individual_non_dep_deduction(
            person, period, sim.tax_benefit_system.parameters, ~head_pensioner
        ),
        dtype=float,
    )
    first_member = {}
    for p, row in enumerate(person_rows):
        first_member.setdefault(row["family"], p)
    family_head_pensioner = np.array(
        [head_pensioner[first_member[f]] for f in range(len(family_rows))]
    )
    family_pensioner = calc(sim, "council_tax_reduction_pensioner") > 0
    return dict(
        ctr_other=eligible * other,
        ctr_own_scheme_is_heads=family_pensioner == family_head_pensioner,
    )


def pool_under_own_scheme(person_rows, family_rows, v, mask=None):
    """For each family, the household's CTR deductions (a couple's once)
    under that family's own scheme, over the members in mask (everyone by
    default)."""
    mask = np.ones(len(person_rows), dtype=bool) if mask is None else mask
    person_household = np.array([row["household"] for row in person_rows])
    family_household = np.array([row["household"] for row in family_rows])
    pools = {}
    for scheme, amounts in (("head", v["ctr"]), ("other", v["ctr_other"])):
        counted = counted_once_per_couple(person_rows, amounts) * mask
        by_household = np.bincount(
            person_household, weights=counted, minlength=family_household.max() + 1
        )
        pools[scheme] = by_household[family_household]
    return np.where(v["ctr_own_scheme_is_heads"], pools["head"], pools["other"])


def run(population, convert=None):
    situation, person_rows, family_rows = build(population, convert)
    sim = Simulation(situation=situation)
    values = dict(
        uc=calc(sim, "uc_individual_non_dep_deduction"),
        hb=calc(sim, "household_benefits_individual_non_dep_deduction"),
        ctr=calc(sim, "council_tax_reduction_individual_non_dep_deduction"),
        pension_credit=calc(sim, "pension_credit"),
        claims=calc(sim, "council_tax_reduction_claimant_benunit"),
        ctr_share=calc(sim, "council_tax_reduction_joint_liability_share"),
        uc_counted=calc(sim, "uc_non_dependants_counted") > 0,
        **ctr_by_scheme(sim, person_rows, family_rows),
        uc_own_claim=(
            (calc(sim, "benunit_is_rent_liable") > 0)
            & (calc(sim, "is_uc_eligible") > 0)
            & (calc(sim, "claims_universal_credit") > 0)
        ),
    )
    return sim, person_rows, family_rows, values


@PROPERTY_SETTINGS
@given(population)
def test_deductions_match_the_oracle(population):
    sim, person_rows, family_rows, v = run(population)
    exp_uc, exp_hb, exp_ctr, exp_uc_individual = oracle(person_rows, family_rows, **v)
    # 1. Oracle. The members each scheme classes as in-unit non-dependants
    # are exactly the generated non-QYP members.
    kinds = np.array([row["kind"] for row in person_rows])
    for in_unit_variable in (
        "is_benefit_unit_non_dependant_for_universal_credit",
        "is_benefit_unit_non_dependant_for_legacy_benefits",
        "is_benefit_unit_non_dependant_for_council_tax_reduction",
    ):
        assert np.array_equal(
            calc(sim, in_unit_variable) > 0, kinds == "non_dependant"
        ), in_unit_variable
    assert np.allclose(v["uc"], exp_uc_individual, atol=0.01)
    assert np.allclose(calc(sim, "uc_non_dep_deductions"), exp_uc, atol=0.01)
    assert np.allclose(
        calc(sim, "housing_benefit_non_dep_deductions"), exp_hb, atol=0.01
    )
    assert np.allclose(
        calc(sim, "council_tax_reduction_non_dep_deductions"), exp_ctr, atol=0.01
    )

    # HB and CTR eligibility: a non-dependant aged 18 or over, either in a
    # family not liable for rent or within their own benefit unit.
    def eligible(own_family_roles):
        return np.array(
            [
                row["age"] >= 18
                and (
                    family_rows[row["family"]]["role"] == "non_dependant"
                    or (
                        row["kind"] == "non_dependant"
                        and family_rows[row["family"]]["role"] in own_family_roles
                    )
                )
                for row in person_rows
            ]
        )

    # Any family's own non-dependants, a boarder's or lodger's included. HB
    # eligibility also excludes an exempt non-dependant (reg 74(7)-(10)); CTR
    # applies its exemptions in the amount.
    everyone = eligible(("head", "sharer", "lodger", "non_dependant"))
    hb_exempt = calc(sim, "housing_benefit_non_dep_deduction_exempt") > 0
    assert np.array_equal(
        calc(sim, "housing_benefit_individual_non_dep_deduction_eligible") > 0,
        everyone & ~hb_exempt,
    )
    assert np.array_equal(
        calc(sim, "council_tax_reduction_individual_non_dep_deduction_eligible") > 0,
        everyone,
    )


@PROPERTY_SETTINGS
@given(population)
def test_conservation_and_exemptions(population):
    sim, person_rows, family_rows, v = run(population)
    ages = np.array([row["age"] for row in person_rows])
    kinds = np.array([row["kind"] for row in person_rows])
    # 2. Conservation. HB: each deduction, a couple's once, is borne in full
    # across the joint occupiers, and a lodger's own non-dependant once more
    # by the lodger, where no claimant is exempt.
    hb_counted = counted_once_per_couple(person_rows, v["hb"])
    hb_families = sim.map_result(
        calc(sim, "housing_benefit_non_dep_deductions"), "benunit", "household"
    )
    lodgers_own = np.array(
        [
            row["kind"] == "non_dependant"
            and family_rows[row["family"]]["role"] == "lodger"
            for row in person_rows
        ]
    )
    hb_people = sim.map_result(hb_counted * (1 + lodgers_own), "person", "household")
    hb_exempt = (
        sim.map_result(
            calc(sim, "housing_benefit_non_dep_deductions_claimant_exempt"),
            "benunit",
            "household",
        )
        > 0
    )
    assert np.allclose(hb_families[~hb_exempt], hb_people[~hb_exempt], atol=0.01)
    assert np.all(hb_families <= hb_people + 0.01)
    # CTR: every non-dependant is borne by each claiming family, under its
    # own scheme, in proportion to its joint-liability share (which follows
    # the regulations' per-person wording, so shares need not sum to one);
    # none where the applicant is exempt. This holds on the generator's
    # domain (rent > 0, claimants liable for it), where no claiming family's
    # own claimant or partner has a deduction.
    ctr_families = calc(sim, "council_tax_reduction_non_dep_deductions")
    expected_ctr = (
        v["claims"]
        * v["ctr_share"]
        * pool_under_own_scheme(person_rows, family_rows, v)
    )
    ctr_exempt = calc(sim, "council_tax_reduction_applicant_has_non_dep_exemption") > 0
    assert np.allclose(ctr_families[~ctr_exempt], expected_ctr[~ctr_exempt], atol=0.01)
    assert np.all(ctr_families[ctr_exempt] == 0)
    # UC: each contribution is borne once, except where the bearer is exempt.
    uc_families = sim.map_result(
        calc(sim, "uc_non_dep_deductions"), "benunit", "household"
    )
    uc_people = sim.map_result(v["uc"], "person", "household")
    assert np.all(uc_families <= uc_people + 0.01)
    # 3. Exemptions.
    renter_exempt = calc(sim, "uc_non_dep_deductions_renter_exempt") > 0
    assert np.all(calc(sim, "uc_non_dep_deductions")[renter_exempt] == 0)
    hb_claimant_exempt = (
        calc(sim, "housing_benefit_non_dep_deductions_claimant_exempt") > 0
    )
    assert np.all(
        calc(sim, "housing_benefit_non_dep_deductions")[hb_claimant_exempt] == 0
    )
    assert np.all(v["uc"][ages < 21] == 0)
    assert np.all(v["hb"][ages < 18] == 0)
    assert np.all(v["ctr"][ages < 18] == 0)
    # Nobody in a family liable for rent is charged except its own
    # non-dependants.
    not_non_dependant = kinds != "non_dependant"
    liable_family = np.array(
        [family_rows[row["family"]]["role"] != "non_dependant" for row in person_rows]
    )
    for amounts in (v["uc"], v["hb"], v["ctr"]):
        assert np.all(amounts[not_non_dependant & liable_family] == 0)


@PROPERTY_SETTINGS
@given(population)
def test_no_op_without_non_dependants_in_a_benefit_unit(population):
    every_kind_dependant = {kind: "dependant" for kind in KINDS}
    sim, person_rows, family_rows, v = run(population, every_kind_dependant)
    # 4. The previous formulas: only members of other families (a couple's
    # higher amount once), charged to the claim that counts them (UC), by rent share
    # (HB) or by claim share (CTR), with the claimants' exemptions.
    person_household = np.array([row["household"] for row in person_rows])
    family_household = np.array([row["household"] for row in family_rows])
    other = calc(sim, "is_non_dependant_of_household_head") > 0

    def other_families(amounts):
        by_household = np.bincount(
            person_household,
            weights=amounts * other,
            minlength=family_household.max() + 1,
        )
        return by_household[family_household]

    renter_exempt = calc(sim, "uc_non_dep_deductions_renter_exempt") > 0
    assert np.allclose(
        calc(sim, "uc_non_dep_deductions"),
        np.where(renter_exempt, 0, v["uc_counted"] * other_families(v["uc"])),
        atol=0.01,
    )
    hb_claimant_exempt = (
        calc(sim, "housing_benefit_non_dep_deductions_claimant_exempt") > 0
    )
    hb_counted = counted_once_per_couple(person_rows, v["hb"])
    assert np.allclose(
        calc(sim, "housing_benefit_non_dep_deductions"),
        np.where(
            hb_claimant_exempt,
            0,
            calc(sim, "share_of_household_rent") * other_families(hb_counted),
        ),
        atol=0.01,
    )
    ctr_exempt = calc(sim, "council_tax_reduction_applicant_has_non_dep_exemption") > 0
    pool = pool_under_own_scheme(person_rows, family_rows, v, mask=other)
    assert np.allclose(
        calc(sim, "council_tax_reduction_non_dep_deductions"),
        np.where(ctr_exempt, 0, v["claims"] * v["ctr_share"] * pool),
        atol=0.01,
    )


# 5-6. The English working-age local schemes. Each council's weekly scale for
# 2026-27 (the parameters' first values, which also apply in 2025): Merton
# para 30, Kingston upon Thames para 30A, Newham para 30B, Westminster
# Appendix A and Oxford para 43.
LOCAL_SCHEMES = {
    "MERTON": dict(
        name="merton",
        thresholds=[0, 279, 485, 605],
        amounts=[5.20, 10.60, 13.30, 15.95],
        benefit_exemptions=True,
        each_uc_couple_member=True,
    ),
    "KINGSTON_UPON_THAMES": dict(
        name="kingston_upon_thames",
        thresholds=[0, 279, 485, 605],
        amounts=[5.64, 11.50, 14.43, 17.31],
        benefit_exemptions=True,
        each_uc_couple_member=True,
    ),
    "NEWHAM": dict(
        name="newham",
        thresholds=[0, 183, 316, 394],
        amounts=[7.54, 14.96, 18.84, 22.61],
        benefit_exemptions=True,
        each_uc_couple_member=False,
    ),
    "WESTMINSTER": dict(
        name="westminster",
        thresholds=[0, 279, 485, 605],
        amounts=[5.20, 10.60, 13.30, 15.95],
        benefit_exemptions=True,
        each_uc_couple_member=False,
    ),
    "OXFORD": dict(
        name="oxford",
        thresholds=[0, 279, 485, 605],
        amounts=[5.20, 10.60, 13.30, 15.95],
        benefit_exemptions=False,
        each_uc_couple_member=False,
    ),
}
EARNINGS = [0, 2_600, 15_600, 30_000]
HOURS = [0, 10, 37.5]


@st.composite
def local_family(draw, role):
    # Working-age adults; the head's family has the household's oldest
    # member, below State Pension age, and every extra member is at most 60.
    adult_age = st.integers(61, 65) if role == "head" else st.integers(25, 59)
    n = draw(st.integers(1, 2))

    def adults(strategy):
        return draw(st.lists(strategy, min_size=n, max_size=n))

    return dict(
        role=role,
        adult_ages=adults(adult_age),
        adult_earnings=adults(st.sampled_from(EARNINGS)),
        adult_hours=adults(st.sampled_from(HOURS)),
        extras=draw(st.lists(extra_member(), min_size=0, max_size=2)),
        extra_students=draw(st.lists(st.booleans(), min_size=2, max_size=2)),
        child=draw(st.booleans()),
        renter_pip=draw(st.booleans()),
        payment=draw(st.floats(1_000, 10_000, allow_nan=False)),
        would_claim_uc=draw(st.booleans()),
    )


@st.composite
def local_household(draw):
    head = draw(local_family("head"))
    others = [
        draw(local_family(draw(st.sampled_from(ROLES))))
        for _ in range(draw(st.integers(0, 2)))
    ]
    return dict(
        families=[head] + others,
        rent=draw(st.floats(3_000, 20_000, allow_nan=False)),
        tenure=draw(st.sampled_from(["RENT_FROM_COUNCIL", "RENT_PRIVATELY"])),
        local_authority=draw(st.sampled_from(sorted(LOCAL_SCHEMES))),
    )


local_population = st.lists(local_household(), min_size=1, max_size=5)


def build_local(population, zero_extra_earnings=False):
    """build(), plus each adult's earnings and hours, each person's education
    (an extra member may be a full-time student), each family's Universal
    Credit claim and each household's council in England."""
    situation, person_rows, family_rows = build(population)
    people = list(situation["people"].values())
    row_iter = iter(zip(people, person_rows))
    for h, house in enumerate(population):
        situation["households"][f"h{h}"].update(
            country="ENGLAND", local_authority=house["local_authority"]
        )
        for f, fam in enumerate(house["families"]):
            situation["benunits"][f"h{h}_f{f}"]["would_claim_uc"] = fam[
                "would_claim_uc"
            ]
            members = (
                [("adult", i) for i in range(len(fam["adult_ages"]))]
                + [("extra", i) for i in range(len(fam["extras"]))]
                + ([("child", 0)] if fam["child"] else [])
            )
            for kind, i in members:
                person, row = next(row_iter)
                if kind == "adult":
                    earnings = fam["adult_earnings"][i]
                    hours = fam["adult_hours"][i]
                    student = False
                elif kind == "extra":
                    earnings = person["employment_income"]
                    if zero_extra_earnings:
                        earnings = 0.0
                    hours = person["weekly_hours"]
                    student = fam["extra_students"][i]
                else:
                    earnings, hours, student = 0.0, 0.0, False
                person.update(
                    employment_income=float(earnings),
                    weekly_hours=float(hours),
                    current_education="TERTIARY" if student else "NOT_IN_EDUCATION",
                )
                row.update(
                    earnings=float(earnings),
                    hours=float(hours),
                    student=student,
                    claimant_or_partner=kind == "adult",
                    local_authority=house["local_authority"],
                )
    return situation, person_rows, family_rows


def weekly_scale(scheme, weekly_income):
    amounts = [
        amount
        for threshold, amount in zip(scheme["thresholds"], scheme["amounts"])
        if weekly_income >= threshold
    ]
    return amounts[-1]


def local_oracle(person_rows, family_rows, benefits, on_award, claims, ctr_share):
    """Each person's deduction under their council's scheme and each family's
    total, from the generated structure, the families' Universal Credit awards
    and who is on each award (on_award, read from the model)."""
    n_people, n_families = len(person_rows), len(family_rows)
    individual = np.zeros(n_people)
    counted = np.zeros(n_people)
    for p, row in enumerate(person_rows):
        f = row["family"]
        scheme = LOCAL_SCHEMES[row["local_authority"]]
        # Reg 9: a member of a family not liable for the rent, or an adult in
        # any family's benefit unit who is not its applicant, partner, child
        # or young person; aged 18 or over.
        eligible = row["age"] >= 18 and (
            family_rows[f]["role"] == "non_dependant" or row["kind"] == "non_dependant"
        )
        if not eligible or row["student"]:
            continue
        couple = [
            other
            for other in person_rows
            if other["family"] == f and other["claimant_or_partner"]
        ]
        if row["claimant_or_partner"]:
            income = sum(member["earnings"] for member in couple)
        else:
            income = row["earnings"]
        weekly = (
            weekly_scale(scheme, income / 52)
            if row["hours"] >= 16
            else scheme["amounts"][0]
        )
        exempt = False
        if scheme["benefit_exemptions"]:
            # Para 30(8)(a): the person the award is payable to. Para
            # 30(8)(c): one entitled to Universal Credit, on their own
            # earnings.
            on_income_related = any(
                on_award[b][p]
                for b in (
                    "income_support",
                    "income_based_jsa",
                    "income_related_esa",
                    "pension_credit",
                )
            )
            exempt = on_income_related or (
                on_award["universal_credit"][p] and row["earnings"] <= 0
            )
        individual[p] = 0 if exempt else weekly * 52
    # One deduction for a couple, the higher, or each member's in Merton and
    # Kingston upon Thames where the couple has Universal Credit; any other
    # member separately.
    for f, family in enumerate(family_rows):
        members = [p for p, row in enumerate(person_rows) if row["family"] == f]
        couple = [p for p in members if person_rows[p]["claimant_or_partner"]]
        scheme = LOCAL_SCHEMES[person_rows[members[0]]["local_authority"]]
        each = scheme["each_uc_couple_member"] and benefits[f]["universal_credit"] > 0
        for p in members:
            if p not in couple or each:
                counted[p] = individual[p]
        if couple and not each:
            counted[couple[0]] = max(individual[p] for p in couple)
    totals = np.zeros(n_families)
    pools = np.zeros(n_families)
    for f, family in enumerate(family_rows):
        in_household = [
            p
            for p, row in enumerate(person_rows)
            if family_rows[row["family"]]["household"] == family["household"]
        ]
        own = [
            p
            for p in in_household
            if person_rows[p]["family"] == f
            and person_rows[p]["kind"] != "non_dependant"
        ]
        pools[f] = sum(counted[p] for p in in_household)
        pool = pools[f] - sum(counted[p] for p in own)
        # Para 30(6): no deduction from an applicant who, or whose partner,
        # gets a qualifying disability benefit; another applicant in the
        # household is not exempt by it.
        if not family["renter_pip"]:
            totals[f] = claims[f] * ctr_share[f] * pool
    return individual, totals, pools


def run_local(population, zero_extra_earnings=False):
    situation, person_rows, family_rows = build_local(population, zero_extra_earnings)
    sim = Simulation(situation=situation)
    universal_credit = calc(sim, "universal_credit")
    benefits = [
        {"universal_credit": universal_credit[f]} for f in range(len(family_rows))
    ]
    on_award = {
        b: calc(sim, f"is_on_{b}") > 0
        for b in (
            "income_support",
            "income_based_jsa",
            "income_related_esa",
            "pension_credit",
            "universal_credit",
        )
    }
    return sim, person_rows, family_rows, benefits, on_award


def legal_claims_and_shares(family_rows):
    """Who claims and each claim's share, from the generated structure alone.
    Where a family shares the rent, every family liable for it (the head's
    and each sharer's) is jointly and severally liable for the council tax and
    claims, each person liable bearing an equal share of the tax and of each
    shared non-dependant's deduction (para 29(3)-(4), 30(5)); otherwise the
    head's family claims alone, in full."""
    n = len(family_rows)
    claims, shares = np.zeros(n), np.ones(n)
    for h in {family["household"] for family in family_rows}:
        families = [i for i, f in enumerate(family_rows) if f["household"] == h]
        liable = [i for i in families if family_rows[i]["role"] in ("head", "sharer")]
        shared = any(family_rows[i]["role"] == "sharer" for i in families)
        liable_people = sum(family_rows[i]["n_liable"] for i in liable)
        for i in families:
            if shared:
                claims[i] = i in liable
                shares[i] = 1 / liable_people if i in liable else 1
            else:
                claims[i] = family_rows[i]["role"] == "head"
    return claims, shares


@PROPERTY_SETTINGS
@given(local_population)
def test_local_scheme_deductions_match_the_oracle(population):
    sim, person_rows, family_rows, benefits, on_award = run_local(population)
    claims, ctr_share = legal_claims_and_shares(family_rows)
    # The claims and shares the totals use are the scheme's, not the model's.
    assert np.array_equal(calc(sim, "council_tax_reduction_claimant_benunit"), claims)
    assert np.allclose(
        calc(sim, "council_tax_reduction_joint_liability_share"), ctr_share
    )
    individual, totals, pools = local_oracle(
        person_rows, family_rows, benefits, on_award, claims, ctr_share
    )
    person_council = np.array([row["local_authority"] for row in person_rows])
    family_council = np.array(
        [
            person_council[[r["family"] for r in person_rows].index(f)]
            for f in range(len(family_rows))
        ]
    )
    for council, scheme in LOCAL_SCHEMES.items():
        name = scheme["name"]
        # 5. Each council's variables follow its own scheme and are zero
        # elsewhere.
        assert np.allclose(
            calc(sim, f"{name}_council_tax_reduction_individual_non_dep_deduction"),
            np.where(person_council == council, individual, 0),
            atol=0.01,
        ), name
        assert np.allclose(
            calc(sim, f"{name}_council_tax_reduction_non_dep_deductions"),
            np.where(family_council == council, totals, 0),
            atol=0.01,
        ), name
    # Conservation: no claiming family's own applicant, partner or child has a
    # deduction, so where no applicant is exempt the claiming families of a
    # household together bear its pool times the sum of their shares: the
    # whole pool, each non-dependant once, where the shares sum to one.
    family_totals = sum(
        calc(sim, f"{scheme['name']}_council_tax_reduction_non_dep_deductions")
        for scheme in LOCAL_SCHEMES.values()
    )
    for h in {family["household"] for family in family_rows}:
        families = [i for i, f in enumerate(family_rows) if f["household"] == h]
        if any(family_rows[i]["renter_pip"] for i in families):
            continue
        borne = sum(family_totals[i] for i in families)
        shares = sum(claims[i] * ctr_share[i] for i in families)
        assert np.isclose(borne, shares * pools[families[0]], atol=0.01)
        if np.isclose(shares, 1):
            assert np.isclose(borne, pools[families[0]], atol=0.01)


def with_an_earning_adult_beside_its_claimant(population):
    """Each household plus a family not liable for the rent whose claimant
    works 37.5 hours without earnings beside a 22-year-old earning £30,000,
    and an applicant with no exemption, so the property always binds."""
    family = dict(
        role="non_dependant",
        adult_ages=[40],
        adult_earnings=[0],
        adult_hours=[37.5],
        extras=[
            dict(
                kind="non_dependant",
                age=22,
                earnings=30_000,
                hours=37.5,
                attendance_allowance=False,
            )
        ],
        extra_students=[False, False],
        child=False,
        renter_pip=False,
        payment=1_000.0,
        would_claim_uc=False,
    )
    return [
        dict(
            house,
            families=[dict(house["families"][0], renter_pip=False)]
            + house["families"][1:]
            + [family],
        )
        for house in population
    ]


@PROPERTY_SETTINGS
@given(local_population)
def test_local_scheme_in_unit_earnings_affect_only_their_own_deduction(population):
    population = with_an_earning_adult_beside_its_claimant(population)
    sim, person_rows, *_ = run_local(population)
    without, *_ = run_local(population, zero_extra_earnings=True)
    # 6. Zeroing the earnings of members who are not a claimant or partner
    # leaves every claimant's and partner's deduction unchanged.
    claimant_or_partner = np.array([row["claimant_or_partner"] for row in person_rows])
    for scheme in LOCAL_SCHEMES.values():
        variable = (
            f"{scheme['name']}_council_tax_reduction_individual_non_dep_deduction"
        )
        assert np.allclose(
            calc(sim, variable)[claimant_or_partner],
            calc(without, variable)[claimant_or_partner],
            atol=0.01,
        ), variable
