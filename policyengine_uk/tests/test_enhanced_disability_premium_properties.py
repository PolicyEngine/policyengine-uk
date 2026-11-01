"""Property-based tests for the legacy enhanced disability premium.

The premium's condition for a claimant or partner (HB Regs 2006 Sch 3 para
15(1)(b)-(d); IS Regs 1987 Sch 2 para 13A; HB Regs (NI) 2006 Sch 4 para 15):
an award of the highest-rate DLA care component, the enhanced-rate PIP daily
living component or armed forces independence payment, for a person who has
not attained the qualifying age for State Pension Credit. Northern Ireland
counts AFIP from 24 December 2013 and PIP from 20 June 2016, which the model
reads at 30 April, so from 2017. The single rate applies to a person who is
not a member of a couple, and one couple rate applies where the condition is
met in respect of either or both members (HB Regs 2006 Sch 3 Part 4).

An award needs a positive amount of the benefit. Its rate comes from the
award category or, for an amount entered without its category, from the
amount: one that reaches the top weekly rate less £1, times 52, counts.

Council Tax Reduction schemes name their own awards. Scotland's working-age
scheme (SSI 2021/249 Sch 1 para 14) adds attendance allowance at either rate
from 1 April 2023 and has no age limit from 20 June 2022, which the model
reads from 2023. Merton's and Kingston upon Thames's schemes (Sch 3 para 12)
count the PIP daily living component at either rate and no AFIP; Newham's
counts the PIP daily living component at either rate and AFIP. Wales,
Westminster and every other scheme take the Housing Benefit condition.

Invariants, for the generated populations: single people, couples and lone
parents in each UK nation and in five English councils besides the default
one, at adult ages from 20 to 85, each holding up to two awards drawn from
DLA care and PIP daily living categories, amounts entered without a category,
categories with an explicit amount (zero or part of the rate), attendance
allowance and AFIP:

1. Oracle: enhanced_disability_premium equals the amount the law gives,
   computed here from the award inputs and the parameter rates, and
   council_tax_reduction_enhanced_disability_premium equals the scheme's.
2. No qualifying award: a family in which no claimant or partner has a
   qualifying award gets no premium.
3. Monotone: giving a claimant or partner a qualifying benefit on top of
   their awards never lowers either premium.
4. Bounds: each premium is nil, the single rate or the couple rate, and never
   exceeds two single rates; the couple rate never exceeds two single rates
   in any year.
5. Each scheme against the legacy premium: the Council Tax Reduction premium
   equals the legacy premium in Wales, Northern Ireland and English councils
   without their own list; in Scotland before 2023; never falls below it in
   Scotland from 2023 or in Newham; and in Merton and Kingston upon Thames
   never falls below it unless the legacy premium rests on AFIP alone, in
   which case it is nil unless an under-age member has a PIP daily living
   award.
6. Differential: for a child or young person in Great Britain, the qualifying
   flag matches the oracle, and the enhanced rate in the Housing Benefit
   child premiums (housing_benefit_child_disability_premiums) is paid
   exactly when the flag holds.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import CountryTaxBenefitSystem, Simulation

PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
WEEKS_IN_YEAR = 52
# The weekly tolerance an amount entered without its category gets below the
# top rate (policyengine-uk-data's CATEGORY_THRESHOLD_WEEKLY_TOLERANCE).
TOLERANCE = 1
# Each example builds one simulation with inputs for every year here, so the
# Northern Ireland PIP date (2017) and the Scottish changes (2023) are on
# both sides of their boundaries in every example.
YEARS = [2016, 2017, 2022, 2023, 2026]
# (country, local authority): None keeps the default local authority.
PLACES = [
    ("ENGLAND", None),
    ("ENGLAND", "MERTON"),
    ("ENGLAND", "KINGSTON_UPON_THAMES"),
    ("ENGLAND", "NEWHAM"),
    ("ENGLAND", "WESTMINSTER"),
    ("ENGLAND", "OXFORD"),
    ("WALES", "CARDIFF"),
    ("SCOTLAND", "CITY_OF_EDINBURGH"),
    ("NORTHERN_IRELAND", None),
]
# Award inputs for each kind of award a person can be drawn with. The amounts
# entered without a category clear (6,000) or miss (3,000) the top-rate
# threshold in every year here: (82.30 - 1) * 52 = 4,227.60 in 2016 and
# (114.60 - 1) * 52 = 5,907.20 in 2026.
AWARDS = {
    "dla_care_lowest": {"dla_sc_category": "LOWER"},
    "dla_care_middle": {"dla_sc_category": "MIDDLE"},
    "dla_care_highest": {"dla_sc_category": "HIGHER"},
    "dla_care_top_amount_only": {"dla_sc": 6_000},
    "dla_care_low_amount_only": {"dla_sc": 3_000},
    "dla_care_highest_zero_amount": {"dla_sc_category": "HIGHER", "dla_sc": 0},
    "dla_care_highest_part_amount": {"dla_sc_category": "HIGHER", "dla_sc": 1_000},
    "pip_daily_living_standard": {"pip_dl_category": "STANDARD"},
    "pip_daily_living_enhanced": {"pip_dl_category": "ENHANCED"},
    "pip_daily_living_top_amount_only": {"pip_dl": 6_000},
    "pip_daily_living_low_amount_only": {"pip_dl": 3_000},
    "pip_daily_living_enhanced_zero_amount": {
        "pip_dl_category": "ENHANCED",
        "pip_dl": 0,
    },
    "afip": {"armed_forces_independence_payment": 2_000},
    "attendance_allowance_lower": {"aa_category": "LOWER"},
    "attendance_allowance_higher": {"aa_category": "HIGHER"},
}
QUALIFYING_AWARDS = ["dla_care_highest", "pip_daily_living_enhanced", "afip"]
ADULT_AGES = [20, 30, 45, 60, 64, 66, 67, 70, 85]

system = CountryTaxBenefitSystem()


def award_inputs(awards):
    """Model inputs for a tuple of awards; a later award's input replaces an
    earlier one's."""
    inputs = {}
    for award in awards:
        inputs.update(AWARDS[award])
    return inputs


def amount(inputs, benefit, year):
    """The annual amount of DLA care (dla_sc) or PIP daily living (pip_dl):
    the amount entered, or the rate for the award category."""
    if benefit in inputs:
        return inputs[benefit]
    dwp = system.parameters(year).gov.dwp
    rates = dwp.dla.self_care if benefit == "dla_sc" else dwp.pip.daily_living
    category = inputs.get(f"{benefit}_category", "NONE")
    if category == "NONE":
        return 0
    return getattr(rates, category.lower()) * WEEKS_IN_YEAR


def top_rate_award(inputs, benefit, year):
    """An award at the highest DLA care or enhanced PIP daily living rate: a
    positive amount, and the top category or an amount within the
    tolerance of the top rate."""
    dwp = system.parameters(year).gov.dwp
    if benefit == "dla_sc":
        top_category, top_rate = "HIGHER", dwp.dla.self_care.higher
    else:
        top_category, top_rate = "ENHANCED", dwp.pip.daily_living.enhanced
    annual = amount(inputs, benefit, year)
    top = inputs.get(f"{benefit}_category") == top_category or (
        annual >= (top_rate - TOLERANCE) * WEEKS_IN_YEAR
    )
    return annual > 0 and top


def afip(inputs):
    return inputs.get("armed_forces_independence_payment", 0) > 0


def qualifies(inputs, country, year):
    """The legacy premium's qualifying awards, from the Regulations."""
    if top_rate_award(inputs, "dla_sc", year) or afip(inputs):
        return True
    if top_rate_award(inputs, "pip_dl", year):
        return country != "NORTHERN_IRELAND" or year >= 2017
    return False


def qualifies_for_scheme(inputs, place, year):
    """The scheme's own awards, before its age limit."""
    country, council = place
    any_pip = amount(inputs, "pip_dl", year) > 0
    dla_highest = top_rate_award(inputs, "dla_sc", year)
    if country == "SCOTLAND":
        # SSI 2021/249 Sch 1 para 14(1), with head (g) from 2023.
        attendance_allowance = inputs.get("aa_category") in ("LOWER", "HIGHER")
        return qualifies(inputs, country, year) or (
            attendance_allowance and year >= 2023
        )
    if council in ("MERTON", "KINGSTON_UPON_THAMES"):
        return dla_highest or any_pip
    if council == "NEWHAM":
        return dla_highest or any_pip or afip(inputs)
    return qualifies(inputs, country, year)


def scheme_age_limit(place, year):
    return place[0] != "SCOTLAND" or year < 2023


awards = st.lists(st.sampled_from(sorted(AWARDS)), max_size=2).map(tuple)
adult = st.fixed_dictionaries(dict(age=st.sampled_from(ADULT_AGES), awards=awards))
family = st.fixed_dictionaries(
    dict(
        place=st.sampled_from(PLACES),
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


def household_inputs(country, council):
    inputs = dict(country=country)
    if council is not None:
        inputs["local_authority"] = council
    return every_year(inputs)


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
        households[f"f{i}"] = dict(members=members, **household_inputs(*f["place"]))
    for i, c in enumerate(children):
        members = [f"c{i}_parent", f"c{i}_child"]
        people[members[0]] = every_year(dict(age=35))
        people[members[1]] = every_year(dict(age=c["age"], **award_inputs(c["awards"])))
        benunits[f"c{i}"] = {"members": members}
        households[f"c{i}"] = dict(
            members=members, **household_inputs(c["country"], None)
        )
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
    country = f["place"][0]
    inputs = [award_inputs(a["awards"]) for a in adults_of(f)]
    legacy = any(
        qualifies(x, country, year) and not attained[j] for j, x in enumerate(inputs)
    )
    age_limit = scheme_age_limit(f["place"], year)
    scheme = any(
        qualifies_for_scheme(x, f["place"], year) and not (age_limit and attained[j])
        for j, x in enumerate(inputs)
    )
    return rate * WEEKS_IN_YEAR * legacy, rate * WEEKS_IN_YEAR * scheme


def check_scheme_against_legacy(f, year, attained, edp, ctr):
    """5. Each scheme's premium against the legacy premium."""
    country, council = f["place"]
    if country == "SCOTLAND":
        if year < 2023:
            assert np.isclose(ctr, edp, atol=0.01)
        else:
            assert ctr >= edp - 0.01
    elif council == "NEWHAM":
        assert ctr >= edp - 0.01
    elif council in ("MERTON", "KINGSTON_UPON_THAMES"):
        under_age = [
            award_inputs(a["awards"])
            for j, a in enumerate(adults_of(f))
            if not attained[j]
        ]
        rests_on_afip = edp > 0 and not any(
            top_rate_award(x, "dla_sc", year) or top_rate_award(x, "pip_dl", year)
            for x in under_age
        )
        if not rests_on_afip:
            assert ctr >= edp - 0.01
        elif not any(amount(x, "pip_dl", year) > 0 for x in under_age):
            # AFIP adds nothing to these schemes.
            assert ctr == 0
    else:
        assert np.isclose(ctr, edp, atol=0.01)


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
        # 2. No qualifying award, no premium.
        inputs = [award_inputs(a["awards"]) for a in adults_of(f)]
        if not any(qualifies(x, f["place"][0], year) for x in inputs):
            assert edp[b] == 0
        if not any(qualifies_for_scheme(x, f["place"], year) for x in inputs):
            assert ctr[b] == 0
        # 4. Bounds.
        for annual in (edp[b], ctr[b]):
            assert any(
                np.isclose(annual, x, atol=0.01)
                for x in (0, single_annual, couple_annual)
            )
            assert annual <= 2 * single_annual + 0.01
        check_scheme_against_legacy(f, year, member_attained, edp[b], ctr[b])
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
        assert bool(qualifying[k]) == qualifies(inputs, c["country"], year), (c, year)
        # The disabled child rate: a positive DLA or PIP amount, or AFIP.
        disabled = (
            amount(inputs, "dla_sc", year) > 0
            or amount(inputs, "pip_dl", year) > 0
            or afip(inputs)
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


class NeutraliseDlaCareAndPipDailyLiving(Reform):
    def apply(self):
        self.neutralize_variable("dla_sc")
        self.neutralize_variable("pip_dl")


def test_neutralised_awards_pay_no_enhanced_premium():
    """A reform that neutralises DLA care and PIP daily living leaves their
    categories in place but sets both amounts to zero, so no award remains:
    neither premium nor the child's enhanced rate is paid."""
    year = 2026
    people = dict(
        dla=dict(age=30, dla_sc_category="HIGHER"),
        pip=dict(age=30, pip_dl_category="ENHANCED"),
        parent=dict(age=35),
        child=dict(age=10, dla_sc_category="HIGHER"),
    )
    groups = dict(dla=["dla"], pip=["pip"], family=["parent", "child"])
    situation = dict(
        people={name: every_year(inputs) for name, inputs in people.items()},
        benunits={name: {"members": members} for name, members in groups.items()},
        households={
            name: dict(members=members, **household_inputs("ENGLAND", "MERTON"))
            for name, members in groups.items()
        },
    )
    p = system.parameters(year).gov.dwp
    single_annual = p.disability_premia.enhanced_single * WEEKS_IN_YEAR
    child_annual = (
        p.housing_benefit.premiums.disabled_child
        + p.housing_benefit.premiums.enhanced_disabled_child
    ) * WEEKS_IN_YEAR
    for reform, adult_premium, child_premium, flag in (
        (None, single_annual, child_annual, True),
        (NeutraliseDlaCareAndPipDailyLiving, 0, 0, False),
    ):
        sim = Simulation(situation=situation, reform=reform)
        assert sim.calculate(
            "receives_enhanced_disability_premium_qualifying_benefit", year
        ).tolist() == [flag, flag, False, flag]
        for variable in (
            "enhanced_disability_premium",
            "council_tax_reduction_enhanced_disability_premium",
        ):
            assert np.allclose(
                sim.calculate(variable, year), [adult_premium, adult_premium, 0]
            ), (reform, variable)
        assert np.allclose(
            sim.calculate("housing_benefit_child_disability_premiums", year),
            [0, 0, child_premium],
        ), reform
