"""Property-based tests for the legacy enhanced disability premium.

The premium's condition for a claimant or partner (HB Regs 2006 Sch 3 para
15(1)(b)-(d); IS Regs 1987 Sch 2 para 13A; HB Regs (NI) 2006 Sch 4 para 15):
the highest-rate DLA care component, the enhanced-rate PIP daily living
component or armed forces independence payment, for a person who has not
attained the qualifying age for State Pension Credit. Northern Ireland counts
AFIP from 24 December 2013 and PIP from 20 June 2016, which the model reads
at 30 April, so from 2017. The single rate applies to a person who is not a
member of a couple, and one couple rate applies where the condition is met
in respect of either or both members (HB Regs 2006 Sch 3 Part 4).

Scotland's working-age Council Tax Reduction scheme (SSI 2021/249 Sch 1 para
14) adds attendance allowance at either rate from 1 April 2023 and has no
age limit from 20 June 2022, which the model reads from 2023.

Invariants, for any generated population of single people, couples and lone
parents in every UK nation, of any adult age, with any mix of DLA care, PIP
daily living, attendance allowance and AFIP awards:

1. Oracle: enhanced_disability_premium equals the amount the law gives,
   computed here from the award inputs and the parameter rates, and
   council_tax_reduction_enhanced_disability_premium equals the scheme's.
2. No qualifying benefit: a family in which no claimant or partner receives
   a qualifying benefit gets neither premium.
3. Monotone: giving a claimant or partner a qualifying benefit on top of
   their awards never lowers either premium.
4. Bounds: each premium is nil, the single rate or the couple rate, and never
   exceeds two single rates; the couple rate never exceeds two single rates
   in any year.
5. Differential: outside Scotland, and in Scotland before 2023, the Council
   Tax Reduction premium equals the legacy premium; in Scotland from 2023 it
   is never lower.
6. Differential: for a child or young person in Great Britain, the enhanced
   rate in the Housing Benefit child premiums
   (housing_benefit_child_disability_premiums, which encodes the same
   paragraph 15 list separately) is paid exactly when the child receives a
   qualifying benefit.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
WEEKS_IN_YEAR = 52
# Each example builds one simulation with inputs for every year here, so the
# Northern Ireland PIP date (2017) and the Scottish changes (2023) are on
# both sides of their boundaries in every example.
YEARS = [2016, 2017, 2022, 2023, 2026]
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Award inputs for each kind of award a person can be drawn with.
AWARDS = {
    "dla_care_lowest": {"dla_sc_category": "LOWER"},
    "dla_care_middle": {"dla_sc_category": "MIDDLE"},
    "dla_care_highest": {"dla_sc_category": "HIGHER"},
    "pip_daily_living_standard": {"pip_dl_category": "STANDARD"},
    "pip_daily_living_enhanced": {"pip_dl_category": "ENHANCED"},
    "afip": {"armed_forces_independence_payment": 2_000},
    "attendance_allowance_lower": {"aa_category": "LOWER"},
    "attendance_allowance_higher": {"aa_category": "HIGHER"},
}
QUALIFYING_AWARDS = ["dla_care_highest", "pip_daily_living_enhanced", "afip"]
ADULT_AGES = [20, 30, 45, 60, 64, 66, 67, 70, 85]

system = CountryTaxBenefitSystem()


def award_inputs(awards):
    """Model inputs for a tuple of awards; a later award of the same
    component replaces an earlier one."""
    inputs = {}
    for award in awards:
        inputs.update(AWARDS[award])
    return inputs


def qualifies(inputs, country, year):
    """The legacy premium's qualifying benefits, from the Regulations."""
    if inputs.get("dla_sc_category") == "HIGHER":
        return True
    if inputs.get("armed_forces_independence_payment", 0) > 0:
        return True
    if inputs.get("pip_dl_category") == "ENHANCED":
        return country != "NORTHERN_IRELAND" or year >= 2017
    return False


def qualifies_for_scottish_ctr(inputs, year):
    """SSI 2021/249 Sch 1 para 14(1), with head (g) from 2023."""
    attendance_allowance = inputs.get("aa_category") in ("LOWER", "HIGHER")
    return qualifies(inputs, "SCOTLAND", year) or (
        attendance_allowance and year >= 2023
    )


awards = st.lists(st.sampled_from(sorted(AWARDS)), max_size=2).map(tuple)
adult = st.fixed_dictionaries(dict(age=st.sampled_from(ADULT_AGES), awards=awards))
family = st.fixed_dictionaries(
    dict(
        country=st.sampled_from(COUNTRIES),
        shape=st.sampled_from(["single", "couple", "lone_parent"]),
        adults=st.lists(adult, min_size=2, max_size=2),
        upgrade_member=st.integers(0, 1),
        upgrade_award=st.sampled_from(QUALIFYING_AWARDS),
    )
)
child = st.fixed_dictionaries(
    dict(
        age=st.sampled_from([4, 10, 16, 17]),
        awards=awards,
        country=st.sampled_from(["ENGLAND", "WALES", "SCOTLAND"]),
    )
)


def adults_of(f):
    return f["adults"][: 2 if f["shape"] == "couple" else 1]


def upgraded(f):
    """The same family with one claimant or partner given a qualifying
    benefit on top of their awards."""
    adults = [dict(a) for a in f["adults"]]
    j = f["upgrade_member"] % len(adults_of(f))
    adults[j]["awards"] = adults[j]["awards"] + (f["upgrade_award"],)
    return dict(f, adults=adults)


def every_year(inputs):
    return {k: {year: v for year in YEARS} for k, v in inputs.items()}


def build(families, children):
    """One household and one benefit unit per family, and one per child with
    a parent aged 35. Claimants and partners are marked as such, so no age
    gap reads one as the other's child."""
    people, benunits, households = {}, {}, {}
    for i, f in enumerate(families):
        members = []
        for j, a in enumerate(adults_of(f)):
            name = f"f{i}_adult{j}"
            inputs = dict(
                age=a["age"], is_claimant_or_partner=True, **award_inputs(a["awards"])
            )
            people[name] = every_year(inputs)
            members.append(name)
        if f["shape"] == "lone_parent":
            name = f"f{i}_child"
            people[name] = every_year(dict(age=8, is_claimant_or_partner=False))
            members.append(name)
        benunits[f"f{i}"] = {"members": members}
        households[f"f{i}"] = {
            "members": members,
            "country": every_year(dict(country=f["country"]))["country"],
        }
    for i, c in enumerate(children):
        members = [f"c{i}_parent", f"c{i}_child"]
        people[members[0]] = every_year(dict(age=35))
        people[members[1]] = every_year(dict(age=c["age"], **award_inputs(c["awards"])))
        benunits[f"c{i}"] = {"members": members}
        households[f"c{i}"] = {
            "members": members,
            "country": every_year(dict(country=c["country"]))["country"],
        }
    sim = Simulation(
        situation=dict(people=people, benunits=benunits, households=households)
    )
    person_ids = list(sim.populations["person"].ids)
    benunit_ids = list(sim.populations["benunit"].ids)
    return sim, person_ids.index, benunit_ids.index


def oracle(f, year, attained):
    """The two annual premiums from the law for one family. attained[j] is
    whether adult j has attained the qualifying age for State Pension
    Credit."""
    p = system.parameters(year).gov.dwp.disability_premia
    rate = p.enhanced_couple if f["shape"] == "couple" else p.enhanced_single
    inputs = [award_inputs(a["awards"]) for a in adults_of(f)]
    legacy = any(
        qualifies(x, f["country"], year) and not attained[j]
        for j, x in enumerate(inputs)
    )
    if f["country"] == "SCOTLAND":
        scheme = any(
            qualifies_for_scottish_ctr(x, year) and (not attained[j] or year >= 2023)
            for j, x in enumerate(inputs)
        )
    else:
        scheme = legacy
    return rate * WEEKS_IN_YEAR * legacy, rate * WEEKS_IN_YEAR * scheme


def check_families(sim, person, benunit, families, year):
    n = len(families) // 2
    edp = sim.calculate("enhanced_disability_premium", year)
    ctr = sim.calculate("council_tax_reduction_enhanced_disability_premium", year)
    attained = sim.calculate("has_attained_state_pension_credit_qualifying_age", year)
    is_couple = sim.calculate("is_couple", year)
    p = system.parameters(year).gov.dwp.disability_premia
    single_annual = p.enhanced_single * WEEKS_IN_YEAR
    couple_annual = p.enhanced_couple * WEEKS_IN_YEAR
    family_edp, family_ctr = [], []
    for i, f in enumerate(families):
        b = benunit(f"f{i}")
        member_attained = [
            bool(attained[person(f"f{i}_adult{j}")]) for j in range(len(adults_of(f)))
        ]
        assert bool(is_couple[b]) == (f["shape"] == "couple")
        legacy, scheme = oracle(f, year, member_attained)
        family_edp.append(edp[b])
        family_ctr.append(ctr[b])
        # 1. Oracle.
        assert np.isclose(edp[b], legacy, atol=0.01), (f, year, edp[b], legacy)
        assert np.isclose(ctr[b], scheme, atol=0.01), (f, year, ctr[b], scheme)
        # 2. No qualifying benefit, no premium.
        inputs = [award_inputs(a["awards"]) for a in adults_of(f)]
        if not any(qualifies(x, f["country"], year) for x in inputs):
            assert edp[b] == 0
            if not any(qualifies_for_scottish_ctr(x, year) for x in inputs):
                assert ctr[b] == 0
        # 4. Bounds.
        for amount in (edp[b], ctr[b]):
            assert any(
                np.isclose(amount, x, atol=0.01)
                for x in (0, single_annual, couple_annual)
            )
            assert amount <= 2 * single_annual + 0.01
        # 5. Council Tax Reduction against the legacy premium.
        if f["country"] != "SCOTLAND" or year < 2023:
            assert np.isclose(ctr[b], edp[b], atol=0.01)
        else:
            assert ctr[b] >= edp[b] - 0.01
    # 3. Monotone: the second half are the first half's twins, each with a
    # qualifying benefit added.
    assert all(t >= s - 0.01 for s, t in zip(family_edp[:n], family_edp[n:]))
    assert all(t >= s - 0.01 for s, t in zip(family_ctr[:n], family_ctr[n:]))


def check_children(sim, person, benunit, children, year):
    # 6. The Housing Benefit child premiums' enhanced rate.
    p = system.parameters(year).gov.dwp.housing_benefit.premiums
    premiums = sim.calculate("housing_benefit_child_disability_premiums", year)
    qualifying = sim.calculate(
        "receives_enhanced_disability_premium_qualifying_benefit", year
    )
    young = sim.calculate("is_child_or_young_person_for_legacy_benefits", year)
    for i, c in enumerate(children):
        k = person(f"c{i}_child")
        if not young[k]:
            continue
        inputs = award_inputs(c["awards"])
        # The disabled child rate: any DLA, PIP or AFIP award.
        disabled = any(
            key in inputs
            for key in (
                "dla_sc_category",
                "pip_dl_category",
                "armed_forces_independence_payment",
            )
        )
        weekly = premiums[benunit(f"c{i}")] / WEEKS_IN_YEAR
        enhanced_weekly = weekly - p.disabled_child * disabled
        assert np.isclose(
            enhanced_weekly, p.enhanced_disabled_child * qualifying[k], atol=0.01
        ), (c, year, weekly)


@PROPERTY_SETTINGS
@given(
    families=st.lists(family, min_size=1, max_size=30),
    children=st.lists(child, max_size=15),
)
def test_enhanced_disability_premium_invariants(families, children):
    everyone = families + [upgraded(f) for f in families]
    sim, person, benunit = build(everyone, children)
    for year in YEARS:
        check_families(sim, person, benunit, everyone, year)
        check_children(sim, person, benunit, children, year)


def test_couple_rate_never_exceeds_two_single_rates():
    for year in range(2015, 2031):
        p = system.parameters(year).gov.dwp.disability_premia
        assert p.enhanced_couple <= 2 * p.enhanced_single, year
