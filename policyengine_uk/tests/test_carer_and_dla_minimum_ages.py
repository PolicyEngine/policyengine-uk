"""Minimum-age cash/override contracts using the existing annual FLOAT age.

Other qualifying-care/disability/duration conditions are assumed. These tests
preserve the category/reported-receipt proxies; they do not audit eligibility.
"""

from pathlib import Path

import pytest

from policyengine_core.parameters.helpers import load_parameter_file
from policyengine_uk import CountryTaxBenefitSystem, Simulation

YEAR = 2026


def situation(person, country="ENGLAND"):
    return {
        "people": {
            "caregiver": {"age": {YEAR: 50}, "pip_dl_category": {YEAR: "STANDARD"}},
            "person": {name: {YEAR: value} for name, value in person.items()},
        },
        "benunits": {"family": {"members": ["caregiver", "person"]}},
        "households": {
            "home": {"members": ["caregiver", "person"], "country": {YEAR: country}}
        },
    }


@pytest.mark.parametrize(
    "path,first,minimum",
    [
        ("gov.dwp.carers_allowance.min_age", "2015-01-01", 16),
        (
            "gov.social_security_scotland.carer_support_payment.min_age",
            "2023-11-19",
            16,
        ),
        ("gov.dwp.dla.mobility.higher_min_age", "2001-04-09", 3),
        ("gov.dwp.dla.mobility.lower_min_age", "2001-04-09", 5),
    ],
)
def test_raw_age_dates_and_supported_annual_parameters(path, first, minimum):
    parameter_file = (
        Path(__file__).resolve().parents[1]
        / "parameters"
        / (path.replace(".", "/") + ".yaml")
    )
    raw = load_parameter_file(str(parameter_file), name=path)
    assert raw.values_list[-1].instant_str == first
    assert raw(first) == minimum
    assert raw("2040-01-01") == minimum
    # CA's first date is model coverage, not asserted legal commencement.
    # Statutory CSP dates do not expand the existing annual replacement rule.
    system = CountryTaxBenefitSystem()
    for year in [2015, 2024, 2025, 2026, 2040]:
        node = system.parameters(str(year))
        for part in path.split("."):
            node = getattr(node, part)
        assert node == minimum


@pytest.mark.parametrize("year", [2015, 2024, 2025])
def test_age_gate_keeps_supported_annual_csp_and_ca_routing(year):
    inputs = situation({"age": 15, "care_hours": 35}, "SCOTLAND")
    for person in inputs["people"].values():
        for name, value in person.items():
            person[name] = {year: value[YEAR]}
    inputs["households"]["home"]["country"] = {year: "SCOTLAND"}
    sim = Simulation(situation=inputs)
    assert sim.calculate("carers_allowance", year)[1] == 0
    assert sim.calculate("carer_support_payment", year)[1] == 0


@pytest.mark.parametrize(
    "parameter,raised,person,country,output,baseline,other_person,other_country,other_output,other_cash",
    [
        (
            "gov.dwp.carers_allowance.min_age",
            18,
            {"age": 17, "care_hours": 35},
            "ENGLAND",
            "carers_allowance",
            4495.40,
            {"age": 17, "care_hours": 35},
            "SCOTLAND",
            "carer_support_payment",
            4495.40,
        ),
        (
            "gov.social_security_scotland.carer_support_payment.min_age",
            18,
            {"age": 17, "care_hours": 35},
            "SCOTLAND",
            "carer_support_payment",
            4495.40,
            {"age": 17, "care_hours": 35},
            "ENGLAND",
            "carers_allowance",
            4495.40,
        ),
        (
            "gov.dwp.dla.mobility.higher_min_age",
            4,
            {"age": 3, "dla_m_category": "HIGHER"},
            "ENGLAND",
            "dla_m",
            4160,
            {"age": 5, "dla_m_category": "LOWER"},
            "ENGLAND",
            "dla_m",
            1575.60,
        ),
        (
            "gov.dwp.dla.mobility.lower_min_age",
            6,
            {"age": 5, "dla_m_category": "LOWER"},
            "ENGLAND",
            "dla_m",
            1575.60,
            {"age": 3, "dla_m_category": "HIGHER"},
            "ENGLAND",
            "dla_m",
            4160,
        ),
    ],
)
def test_each_minimum_age_reform_moves_only_its_cash_boundary(
    parameter,
    raised,
    person,
    country,
    output,
    baseline,
    other_person,
    other_country,
    other_output,
    other_cash,
):
    original = Simulation(situation=situation(person, country))
    reformed = Simulation(
        situation=situation(person, country), reform={parameter: raised}
    )
    assert original.calculate(output, YEAR)[1] == pytest.approx(baseline, abs=0.01)
    assert reformed.calculate(output, YEAR)[1] == 0
    countercontrol = Simulation(
        situation=situation(other_person, other_country), reform={parameter: raised}
    )
    assert countercontrol.calculate(other_output, YEAR)[1] == pytest.approx(
        other_cash, abs=0.01
    )


@pytest.mark.parametrize(
    "input_name,output,amount,country,age",
    [
        ("carers_allowance", "carers_allowance", 123, "ENGLAND", 15),
        ("carers_allowance_pre_overlap", "carers_allowance", 234, "ENGLAND", 15),
        ("carer_support_payment", "carer_support_payment", 345, "SCOTLAND", 15),
        (
            "carer_support_payment_pre_overlap",
            "carer_support_payment",
            456,
            "SCOTLAND",
            15,
        ),
        ("dla_m", "dla", 567, "ENGLAND", 1),
    ],
)
def test_explicit_amount_overrides_keep_the_generic_input_contract(
    input_name, output, amount, country, age
):
    # A supplied amount is intentionally an override, not entitlement proof.
    sim = Simulation(situation=situation({"age": age, input_name: amount}, country))
    assert sim.calculate(output, YEAR)[1] == amount


def test_missing_age_keeps_the_existing_default_and_none_category_pays_nothing():
    sim = Simulation(
        situation=situation({"care_hours": 35, "dla_m_category": "HIGHER"})
    )
    assert sim.calculate("age", YEAR)[1] == 40
    assert sim.calculate("carers_allowance", YEAR)[1] == pytest.approx(
        4495.40, abs=0.01
    )
    assert sim.calculate("dla_m", YEAR)[1] == 4160
    none = Simulation(situation=situation({"age": 40, "dla_m_category": "NONE"}))
    assert none.calculate("dla_m", YEAR)[1] == 0


@pytest.mark.parametrize("reverse", [False, True])
def test_each_persons_age_controls_cash_across_families_and_request_order(reverse):
    people, benunits, households = {}, {}, {}
    specs = [
        ("english", "ENGLAND", 15, 3),
        ("scottish", "SCOTLAND", 16, 2),
    ]
    for family, country, carer_age, child_age in specs:
        names = [family + suffix for suffix in ["_caree", "_carer", "_child"]]
        facts = [
            {"age": 50, "pip_dl_category": "STANDARD"},
            {"age": carer_age, "care_hours": 35},
            {"age": child_age, "dla_m_category": "HIGHER"},
        ]
        for name, fact in zip(names, facts):
            people[name] = {key: {YEAR: value} for key, value in fact.items()}
        members = list(reversed(names)) if reverse else names
        benunits[family] = {"members": members}
        households[family] = {"members": members, "country": {YEAR: country}}
    if reverse:
        people = dict(reversed(list(people.items())))
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    if reverse:
        sim.calculate("is_entitled_to_carer_benefit", YEAR)
    for variable, expected in [
        ("carers_allowance", {}),
        ("carer_support_payment", {"scottish_carer": 4495.40}),
        ("dla", {"english_child": 4160}),
    ]:
        values = dict(zip(sim.populations["person"].ids, sim.calculate(variable, YEAR)))
        for name, value in values.items():
            assert value == pytest.approx(expected.get(name, 0), abs=0.01)
