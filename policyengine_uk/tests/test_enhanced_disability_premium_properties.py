"""Property-based tests for the legacy enhanced disability premium.

A claimant or partner meets the premium's condition (HB Regs 2006 Sch 3 para
15(1)(b)-(d); IS Regs 1987 Sch 2 para 13A; HB Regs (NI) 2006 Sch 4 para 15)
with an award of the highest-rate DLA care component, the enhanced-rate PIP
daily living component or armed forces independence payment, while under the
qualifying age for State Pension Credit. Claimants in Northern Ireland qualify
through AFIP from 24 December 2013 and through PIP from 20 June 2016, which
the model reads at 30 April, so from 2017. Housing Benefit pays the single
rate to a person who is not a member of a couple, and one couple rate where
either or both members meet the condition (HB Regs 2006 Sch 3 Part 4).

The model counts an award only with a positive amount of the benefit, and
takes its rate from the award category or from an amount that reaches
52 × (top weekly rate − £1).

Scottish councils count attendance allowance at either rate from 1 April 2023
(SSI 2021/249 Sch 1 para 14), and the Scottish Ministers removed the age limit
from 20 June 2022, which the model reads from 2023. Merton and Kingston upon
Thames (Sch 3 para 12) count the PIP daily living component at either rate
and omit AFIP; Newham counts the PIP daily living component at either rate
and AFIP. In Westminster the model applies the Default Scheme's list (S.I.
2012/2886 Sch 3 para 12), which counts the PIP daily living component at
either rate and omits AFIP. Each council's list starts on or before 1 April
2013 (COUNCIL_LISTS) and applies in every model year, except that for
Kingston upon Thames the model assumes the Housing Benefit condition in
2018-19 to 2022-23, for which no complete scheme text survives. The model
also applies the Housing Benefit condition in Wales and every other scheme.

The test generates single people, couples and lone parents in the places and
age range below, with the listed awards, and adds a family in each council
with its own list to every example. It supplies each person's entered DLA
care and PIP daily living amount, or computes an amount from their category.
It checks these invariants in every year from 2015 to 2030:

1. The test computes the statutory amount from the award inputs and the
   parameter rates. enhanced_disability_premium equals that amount, and
   council_tax_reduction_enhanced_disability_premium equals the amount under
   the scheme's own list.
2. The model pays no premium to a family in which no claimant or partner has
   a qualifying award.
3. Giving a claimant or partner a qualifying benefit on top of their awards
   never lowers either premium.
4. Each premium equals nil, the single rate or the couple rate, and never
   exceeds two single rates; the couple rate never exceeds two single rates
   in any year.
5. The Council Tax Reduction premium equals the legacy premium in Wales,
   Northern Ireland, Oxford and the default English council, in Scotland
   before 2023, and in Kingston upon Thames in 2018-19 to 2022-23. It never
   falls below the legacy premium in Scotland from 2023, or where a council's
   own list counts AFIP (Newham's). Where a council's own list omits AFIP
   (Merton's, Kingston upon Thames's and Westminster's), it never falls
   below the legacy premium unless that premium rests on AFIP alone, and then
   the model pays none unless an under-age claimant or partner has a PIP
   daily living award.
6. For a child or young person in Great Britain, the qualifying flag matches
   the test's own calculation. The model pays the child's enhanced rate in the
   Housing Benefit child premiums (housing_benefit_child_disability_premiums)
   when the flag holds and pays none when it does not.
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
# The test allows this weekly tolerance below the top rate
# (policyengine-uk-data's CATEGORY_THRESHOLD_WEEKLY_TOLERANCE).
TOLERANCE = 1
# Each example builds one simulation with inputs for every year from 2015 to
# 2030, so every example tests both sides of the Northern Ireland PIP date
# (2017) and the Scottish changes (2023). Every council's own list starts in
# 2013-14, before the model's first year, so the test checks each list in
# every year.
YEARS = list(range(2015, 2031))
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
# The generator assigns the award inputs below. The reported amounts of 7,000
# and 3,000 respectively exceed and fall below each tested year's threshold,
# which rises from (82.30 - 1) * 52 = 4,227.60 in 2015 to 6,596.16 at the
# model's uprated 2030 rates (test_entered_amounts_straddle_the_threshold).
AWARDS = {
    "dla_care_lowest": {"dla_sc_category": "LOWER"},
    "dla_care_middle": {"dla_sc_category": "MIDDLE"},
    "dla_care_highest": {"dla_sc_category": "HIGHER"},
    "dla_care_top_amount_only": {"dla_sc": 7_000},
    "dla_care_low_amount_only": {"dla_sc": 3_000},
    "dla_care_highest_zero_amount": {"dla_sc_category": "HIGHER", "dla_sc": 0},
    "dla_care_highest_part_amount": {"dla_sc_category": "HIGHER", "dla_sc": 1_000},
    "pip_daily_living_standard": {"pip_dl_category": "STANDARD"},
    "pip_daily_living_enhanced": {"pip_dl_category": "ENHANCED"},
    "pip_daily_living_top_amount_only": {"pip_dl": 7_000},
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
# Each council's own list (Sch 3 para 12 of its scheme), by the scheme year
# it starts: "dla_highest" is the DLA care component at the highest rate,
# "any_pip" the PIP daily living component at either rate and "afip" armed
# forces independence payment. None marks years where the model applies the
# Housing Benefit condition instead.
COUNCIL_LISTS = {
    # The 2013 rules.
    "MERTON": {2013: ("dla_highest", "any_pip")},
    # The Default Scheme, adopted for 2013-14. No complete scheme text for
    # 2018-19 to 2022-23 survives, so the model assumes the Housing Benefit
    # condition in those years.
    "KINGSTON_UPON_THAMES": {
        2013: ("dla_highest", "any_pip"),
        2018: None,
        2023: ("dla_highest", "any_pip"),
    },
    # The 2013 scheme, and the 2014 scheme with AFIP.
    "NEWHAM": {
        2013: ("dla_highest", "any_pip"),
        2014: ("dla_highest", "any_pip", "afip"),
    },
    # The Default Scheme: the council has approved the same scheme since
    # 2013-14, and its Cabinet says the council's scheme mirrors it.
    "WESTMINSTER": {2013: ("dla_highest", "any_pip")},
}

system = CountryTaxBenefitSystem()


def award_inputs(awards):
    """Return the model inputs for a tuple of awards, letting a later award's
    input replace an earlier one's."""
    inputs = {}
    for award in awards:
        inputs.update(AWARDS[award])
    return inputs


def amount(inputs, benefit, year):
    """Return the entered annual amount of DLA care (dla_sc) or PIP daily
    living (pip_dl), or compute it from the award category."""
    if benefit in inputs:
        return inputs[benefit]
    dwp = system.parameters(year).gov.dwp
    rates = dwp.dla.self_care if benefit == "dla_sc" else dwp.pip.daily_living
    category = inputs.get(f"{benefit}_category", "NONE")
    if category == "NONE":
        return 0
    return getattr(rates, category.lower()) * WEEKS_IN_YEAR


def top_rate_award(inputs, benefit, year):
    """Check for an award at the highest DLA care or enhanced PIP daily living
    rate: a positive amount and either the top category or an amount within
    the tolerance of the top rate."""
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
    """Check for the legacy premium's qualifying awards under the
    Regulations."""
    if top_rate_award(inputs, "dla_sc", year) or afip(inputs):
        return True
    if top_rate_award(inputs, "pip_dl", year):
        return country != "NORTHERN_IRELAND" or year >= 2017
    return False


def council_list(council, year):
    """Return the awards on a council's own list in a year, or None where
    the model applies the Housing Benefit condition."""
    starts = [start for start in COUNCIL_LISTS.get(council, {}) if start <= year]
    return COUNCIL_LISTS[council][max(starts)] if starts else None


def qualifies_for_scheme(inputs, place, year):
    """Check for the scheme's own awards, before its age limit."""
    country, council = place
    if country == "SCOTLAND":
        # SSI 2021/249 Sch 1 para 14(1), with head (g) from 2023.
        attendance_allowance = inputs.get("aa_category") in ("LOWER", "HIGHER")
        return qualifies(inputs, country, year) or (
            attendance_allowance and year >= 2023
        )
    listed = council_list(council, year)
    if listed is None:
        # The Housing Benefit condition.
        return qualifies(inputs, country, year)
    held = dict(
        dla_highest=top_rate_award(inputs, "dla_sc", year),
        any_pip=amount(inputs, "pip_dl", year) > 0,
        afip=afip(inputs),
    )
    return any(held[award] for award in listed)


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
# A family in each council with its own list, drawn for every example.
council_families = st.tuples(
    *(
        family.map(lambda f, place=place: dict(f, place=place))
        for place in PLACES
        if place[1] in COUNCIL_LISTS
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
    """Add a qualifying benefit to one claimant's or partner's awards and
    return the family."""
    adults = [dict(a) for a in f["adults"]]
    j = f["upgrade_member"] % len(adults_of(f))
    adults[j]["awards"] = adults[j]["awards"] + (f["upgrade_award"],)
    return dict(f, adults=adults)


def every_year(inputs):
    return {k: {year: v for year in YEARS} for k, v in inputs.items()}


def person_inputs(age, awards, **extra):
    """Return a person's inputs for every year. A situation that supplies an
    amount for one person supplies the default, zero, for everyone else, as
    it does for categories (utils/pip.py). So the test gives every person
    both amounts: the amount entered, or the rate for the award category,
    which the amount formulas would give."""
    inputs = award_inputs(awards)
    person = every_year(dict(age=age, **extra, **inputs))
    for benefit in ("dla_sc", "pip_dl"):
        person[benefit] = {year: amount(inputs, benefit, year) for year in YEARS}
    return person


def household_inputs(country, council):
    inputs = dict(country=country)
    if council is not None:
        inputs["local_authority"] = council
    return every_year(inputs)


def build(families, children):
    """Build one household and one benefit unit per family, and one per child
    with a parent aged 35. The test marks claimants and partners as such, so
    the model never reads an age gap as making one the other's child."""
    people, benunits, households = {}, {}, {}
    for i, f in enumerate(families):
        members = []
        for j, a in enumerate(adults_of(f)):
            name = f"f{i}_adult{j}"
            people[name] = person_inputs(
                a["age"], a["awards"], is_claimant_or_partner=True
            )
            members.append(name)
        if f["shape"] == "lone_parent":
            name = f"f{i}_child"
            people[name] = person_inputs(8, (), is_claimant_or_partner=False)
            members.append(name)
        benunits[f"f{i}"] = {"members": members}
        households[f"f{i}"] = dict(members=members, **household_inputs(*f["place"]))
    for i, c in enumerate(children):
        members = [f"c{i}_parent", f"c{i}_child"]
        people[members[0]] = person_inputs(35, ())
        people[members[1]] = person_inputs(c["age"], c["awards"])
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
    """Compute the two annual premiums under the law for one family.
    attained[j] holds when adult j has attained the qualifying age for State
    Pension Credit."""
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
    """Check invariant 5: each scheme's premium against the legacy
    premium."""
    country, council = f["place"]
    listed = council_list(council, year)
    if country == "SCOTLAND":
        if year < 2023:
            assert np.isclose(ctr, edp, atol=0.01)
        else:
            assert ctr >= edp - 0.01
    elif listed is None:
        assert np.isclose(ctr, edp, atol=0.01)
    elif "afip" in listed:
        assert ctr >= edp - 0.01
    else:
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
            # The list omits AFIP.
            assert ctr == 0


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
    # 3. Monotone: the test pairs each family in the first half with its twin
    # in the second half, which has a qualifying benefit added.
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
        # A child qualifies for the disabled child rate with a positive DLA or
        # PIP amount, or AFIP.
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
    council_families=council_families,
    children=st.lists(child, max_size=15),
)
def test_enhanced_disability_premium_invariants(families, council_families, children):
    families = families + list(council_families)
    everyone = families + [upgraded(f) for f in families]
    sim, person, benunit = build(everyone, children)
    for year in YEARS:
        check_families(sim, person, benunit, everyone, year)
        check_children(sim, person, benunit, children, year)


def test_couple_rate_never_exceeds_two_single_rates():
    for year in range(2015, 2031):
        p = system.parameters(year).gov.dwp.disability_premia
        assert p.enhanced_couple <= 2 * p.enhanced_single, year


def test_entered_amounts_straddle_the_threshold():
    """In every tested year the entered top amount reaches the top-rate
    threshold and the entered low amount falls below it."""
    for year in YEARS:
        for benefit, award in (("dla_sc", "dla_care"), ("pip_dl", "pip_daily_living")):
            top = AWARDS[f"{award}_top_amount_only"]
            low = AWARDS[f"{award}_low_amount_only"]
            assert top_rate_award(top, benefit, year), (award, year)
            assert not top_rate_award(low, benefit, year), (award, year)


class NeutraliseDlaCareAndPipDailyLiving(Reform):
    def apply(self):
        self.neutralize_variable("dla_sc")
        self.neutralize_variable("pip_dl")


def test_neutralised_awards_pay_no_enhanced_premium():
    """A reform that neutralises DLA care and PIP daily living leaves their
    categories in place but sets both amounts to zero, so no award remains.
    The model then pays neither adult premium nor the child's disability
    premiums."""
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
