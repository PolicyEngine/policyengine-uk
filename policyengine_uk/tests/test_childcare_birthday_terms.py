"""England's base hours begin with the term after the qualifying birthday.

DfE guidance effective 1 April 2026, A1.2/A1.7, and SI 2014/2147 reg 3
provide the birthday bands. A1.4 retains targeted provision until universal
eligibility begins; A1.11 allocates the first hours within working-parent
provision. The calendar oracle uses no implementation date or term helper.
https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026
https://www.legislation.gov.uk/uksi/2014/2147/regulation/3

The retained annual model uses three equal terms and national-average funding
proxies, not actual provider term lengths or fees. The 2026 rates stay fixed
for all three terms, including January 2027. Supplied legacy annual amounts
or shares retain their original opaque annual calculation, without a claim
that they describe individual terms.
"""

from datetime import date
from decimal import Decimal

import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.supplied_inputs import set_model_value

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
VALUES = (
    "universal_childcare_entitlement",
    "targeted_childcare_entitlement",
    "extended_childcare_entitlement_total_per_child",
    "extended_childcare_entitlement_per_child",
)
U, T, W, E = VALUES
TERMS = (date(YEAR, 4, 1), date(YEAR, 9, 1), date(YEAR + 1, 1, 1))
RATES = (Decimal("12.04"), Decimal("8.90"), Decimal("6.61"))


def age_on_6_october(born, year=YEAR):
    return year - born.year - ((10, 6) < (born.month, born.day))


def birthday(born, years):
    try:
        return born.replace(year=born.year + years)
    except ValueError:
        # Either leap-day anniversary falls in the same statutory term band.
        return date(born.year + years, 2, 28)


def situation(
    born=date(2023, 10, 7),
    *,
    age=None,
    targeted=True,
    working=False,
    claims_universal=True,
    claims_targeted=True,
    child_hours=30,
    family_hours=30,
    country="ENGLAND",
    deferred=False,
    annual_inputs=None,
):
    child = {
        "age": {YEAR: age_on_6_october(born) if age is None else age},
        "max_free_entitlement_hours_used": {YEAR: child_hours},
        "early_years_school_start_deferred": {YEAR: deferred},
    }
    if born is not None:
        child["date_of_birth"] = {YEAR: int(born.strftime("%Y%m%d"))}
    for variable, value in (annual_inputs or {}).items():
        child[variable] = {YEAR: value}
    return {
        "people": {"child": child},
        "benunits": {
            "family": {
                "members": ["child"],
                "targeted_childcare_entitlement_eligible": {YEAR: targeted},
                "extended_childcare_entitlement_eligible": {YEAR: working},
                "would_claim_universal_childcare": {YEAR: claims_universal},
                "would_claim_targeted_childcare": {YEAR: claims_targeted},
                "maximum_extended_childcare_hours_usage": {YEAR: family_hours},
            }
        },
        "households": {"home": {"members": ["child"], "country": {YEAR: country}}},
    }


def simulate(*args, reform=None, **kwargs):
    return Simulation(situation=situation(*args, **kwargs), reform=reform)


def amounts(simulation):
    return {
        variable: float(simulation.calculate(variable, YEAR)[0]) for variable in VALUES
    }


def calendar_reference(born, *, targeted, working, claims_universal, claims_targeted):
    """Source rules, term by term, at full usage and the unchanged 2026 proxy."""
    second, third, fourth = (birthday(born, n) for n in (2, 3, 4))
    school = date(fourth.year + (fourth >= date(fourth.year, 9, 1)), 9, 1)
    out = {variable: Decimal(0) for variable in VALUES}
    universal_terms = []
    for start in TERMS:
        before_school = start < school
        universal = third < start and before_school
        target = targeted and second < start <= third and before_school
        universal_terms.append(universal)
        rate = RATES[2] if third < start else RATES[1] if second < start else RATES[0]
        base = Decimal(190) * rate  # 570 / 3, unchanged equal-term convention.
        total = Decimal(380) * rate if working and before_school else Decimal(0)
        universal_value = (
            base if universal and (claims_universal or total) else Decimal(0)
        )
        targeted_value = base if target and (claims_targeted or total) else Decimal(0)
        out[U] += universal_value
        out[T] += targeted_value
        out[W] += total
        out[E] += max(total - universal_value - targeted_value, Decimal(0))
    return {k: float(v) for k, v in out.items()}, any(universal_terms)


@pytest.mark.parametrize(
    "born",
    [
        date(2023, 3, 31),
        date(2023, 4, 1),
        date(2023, 8, 31),
        date(2023, 9, 1),
        date(2023, 10, 6),
        date(2023, 10, 7),
        date(2023, 12, 31),
        date(2024, 1, 1),
    ],
)
@pytest.mark.parametrize("working,claim", [(False, True), (True, True), (True, False)])
def test_calendar_birthday_terms_and_first_hours_allocation(born, working, claim):
    simulation = simulate(
        born, working=working, claims_universal=claim, claims_targeted=claim
    )
    expected, eligible = calendar_reference(
        born,
        targeted=True,
        working=working,
        claims_universal=claim,
        claims_targeted=claim,
    )
    assert amounts(simulation) == pytest.approx(expected, abs=0.01)
    assert (
        bool(simulation.calculate("universal_childcare_entitlement_eligible", YEAR)[0])
        is eligible
    )


def test_a_new_targeted_term_uses_its_qualifying_band():
    simulation = simulate(date(2024, 10, 7), working=True, claims_targeted=False)
    # SOURCE: 190 targeted hours in January at £8.90; working hours use
    # £12.04 in April/September and £8.90 in January, not an age-1 rate all year.
    assert amounts(simulation) == pytest.approx(
        {U: 0, T: 1691, W: 12532.40, E: 10841.40}, abs=0.01
    )


def test_no_targeted_route_does_not_erase_universal_or_working_hours():
    simulation = simulate(date(2023, 8, 31), targeted=False, working=True)
    assert amounts(simulation) == pytest.approx(
        {U: 2511.80, T: 0, W: 8405.60, E: 5893.80}, abs=0.01
    )


@pytest.mark.parametrize("claim", [False, True])
def test_a_later_working_minimum_counts_only_common_terms(claim):
    # Hypothetical age reform: universal September+January, working January
    # only. Do not multiply the already prorated 2/3 base by a 1/3 share.
    simulation = simulate(
        date(2023, 4, 30),
        targeted=False,
        working=True,
        claims_universal=claim,
        reform={"gov.dfe.extended_childcare_entitlement.young_child_minimum_age": 3.5},
    )
    expected_universal = 2511.80 if claim else 1255.90
    assert amounts(simulation) == pytest.approx(
        {U: expected_universal, T: 0, W: 2511.80, E: 1255.90}, abs=0.01
    )


def test_independent_age_reforms_do_not_bridge_a_gap():
    # The targeted scale still ends at its own third-birthday boundary.
    # Raising universal's minimum to four must not extend targeted provision.
    simulation = simulate(
        date(2023, 4, 30), reform={"gov.dfe.universal_childcare_entitlement.age.min": 4}
    )
    assert amounts(simulation)[U] == 0
    assert amounts(simulation)[T] == pytest.approx(1691, abs=0.01)


def test_whole_age_fallback_matches_the_existing_six_april_birthday():
    implicit = simulate(None, age=3, working=True)
    explicit = simulate(date(2023, 4, 6), working=True)
    assert amounts(implicit) == pytest.approx(amounts(explicit), abs=0.01)
    assert amounts(implicit) == pytest.approx(
        {U: 2511.80, T: 1691, W: 8405.60, E: 4202.80}, abs=0.01
    )


@pytest.mark.parametrize("deferred,universal", [(False, 1255.90), (True, 3767.70)])
def test_the_existing_school_and_deferred_guards_remain(deferred, universal):
    simulation = simulate(
        date(2022, 8, 31), targeted=False, working=True, deferred=deferred
    )
    actual = amounts(simulation)
    assert actual[U] == pytest.approx(universal, abs=0.01)
    assert actual[E] == pytest.approx(universal, abs=0.01)
    assert actual[W] == pytest.approx(2 * universal, abs=0.01)


@pytest.mark.parametrize("which", ["child", "family"])
def test_usage_caps_do_not_remove_standalone_base_hours(which):
    simulation = simulate(
        date(2023, 8, 31),
        working=True,
        child_hours=10 if which == "child" else 30,
        family_hours=10 if which == "family" else 30,
    )
    actual = amounts(simulation)
    base = 4202.80 * (2 / 3 if which == "child" else 1)
    assert actual[U] + actual[T] == pytest.approx(base, abs=0.01)
    assert actual[E] == 0


@pytest.mark.parametrize(
    "name,value,expected",
    [
        ("early_years_term_share_before_school", 0, {U: 0, T: 0, W: 0, E: 0}),
        (
            "early_years_term_share_before_school",
            0.5,
            {U: 1883.85, T: 0, W: 3767.70, E: 1883.85},
        ),
        (
            "early_years_term_share_before_school",
            0.4,
            {U: 1507.08, T: 0, W: 3014.16, E: 1507.08},
        ),
        (
            "early_years_term_share_before_school",
            1,
            {U: 3767.70, T: 0, W: 7535.40, E: 3767.70},
        ),
        (
            "extended_childcare_entitlement_term_share",
            0,
            {U: 3767.70, T: 0, W: 0, E: 0},
        ),
        (
            "extended_childcare_entitlement_term_share",
            0.5,
            {U: 3767.70, T: 0, W: 3767.70, E: 1883.85},
        ),
    ],
)
def test_explicit_legacy_shares_keep_the_original_annual_route(name, value, expected):
    simulation = simulate(
        date(2023, 4, 6), targeted=False, working=True, annual_inputs={name: value}
    )
    assert amounts(simulation) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize(
    "name,value,expected",
    [
        (U, 0, {U: 0, T: 5073, W: 10146, E: 5073}),
        (T, 0, {U: 0, T: 0, W: 10146, E: 10146}),
        (W, 0, {U: 0, T: 5073, W: 0, E: 0}),
        (U, 1000, {U: 1000, T: 5073, W: 10146, E: 4073}),
    ],
)
def test_supplied_annual_amounts_remain_authoritative(name, value, expected):
    simulation = simulate(working=True, annual_inputs={name: value})
    assert amounts(simulation) == pytest.approx(expected, abs=0.01)


def clear_derived_amounts(simulation, *, keep=()):
    for variable in (*VALUES, "universal_childcare_entitlement_eligible"):
        if variable not in keep:
            simulation.delete_arrays(variable, YEAR)


def test_a_warm_calculated_cache_is_not_an_annual_input():
    simulation = simulate(working=True)
    first = amounts(simulation)
    for variable in reversed(VALUES):
        simulation.calculate(variable, YEAR)
    assert amounts(simulation) == first
    assert first == pytest.approx(
        {U: 1255.90, T: 3382, W: 9275.80, E: 4637.90}, abs=0.01
    )


def test_an_equal_entered_value_is_still_authoritative_after_a_warm_cache():
    simulation = simulate(working=True)
    native_universal = simulation.calculate(U, YEAR).copy()
    simulation.set_input(U, YEAR, native_universal)
    clear_derived_amounts(simulation, keep=(U,))
    # Genuine input detection, not equality with a previously calculated array,
    # selects the documented whole legacy route and its snapshot eligibility.
    assert amounts(simulation)[W] == pytest.approx(10146, abs=0.01)
    assert not bool(
        simulation.calculate("universal_childcare_entitlement_eligible", YEAR)[0]
    )


def test_deleting_an_entered_amount_restores_the_native_route():
    simulation = simulate(working=True, annual_inputs={U: 0})
    assert amounts(simulation)[W] == pytest.approx(10146, abs=0.01)
    clear_derived_amounts(simulation)
    assert amounts(simulation)[W] == pytest.approx(9275.80, abs=0.01)


def test_replacing_an_entered_amount_keeps_the_authoritative_route():
    simulation = simulate(working=True, annual_inputs={U: 0})
    amounts(simulation)
    simulation.set_input(U, YEAR, [1000])
    clear_derived_amounts(simulation, keep=(U,))
    assert amounts(simulation) == pytest.approx(
        {U: 1000, T: 5073, W: 10146, E: 4073}, abs=0.01
    )


def test_a_partial_person_input_keeps_core_defaults_and_annual_semantics():
    data = situation(working=True, annual_inputs={U: 0})
    other = {
        key: value.copy() for key, value in data["people"]["child"].items() if key != U
    }
    data["people"]["other"] = other
    data["benunits"]["family"]["members"].append("other")
    data["households"]["home"]["members"].append("other")
    simulation = Simulation(situation=data)
    # Core supplies the variable's default zero for the other person in the
    # same input array. Do not infer per-person term identities from that zero.
    assert list(simulation.calculate(U, YEAR)) == [0, 0]
    assert list(simulation.calculate(W, YEAR)) == pytest.approx(
        [10146, 10146], abs=0.01
    )
    assert list(simulation.calculate(E, YEAR)) == pytest.approx([5073, 5073], abs=0.01)


def test_rebuilding_without_the_annual_input_does_not_keep_legacy_provenance():
    simulation = simulate(working=True, annual_inputs={U: 0})
    amounts(simulation)
    simulation.build_from_situation(situation(working=True))
    assert amounts(simulation) == pytest.approx(
        {U: 1255.90, T: 3382, W: 9275.80, E: 4637.90}, abs=0.01
    )


@pytest.mark.parametrize("kind", ["clone", "branch"])
def test_an_entered_amount_in_a_copy_does_not_change_its_parent(kind):
    simulation = simulate(working=True)
    original = amounts(simulation)
    copied = (
        simulation.clone()
        if kind == "clone"
        else simulation.get_branch("entered_childcare")
    )
    copied.set_input(U, YEAR, [0])
    clear_derived_amounts(copied, keep=(U,))
    assert amounts(copied)[W] == pytest.approx(10146, abs=0.01)
    assert amounts(simulation) == original


def test_a_model_stored_value_is_not_misread_as_a_supplied_amount():
    simulation = simulate(working=True)
    native = simulation.calculate(U, YEAR).copy()
    set_model_value(simulation, U, YEAR, native)
    clear_derived_amounts(simulation, keep=(U,))
    assert amounts(simulation)[W] == pytest.approx(9275.80, abs=0.01)
