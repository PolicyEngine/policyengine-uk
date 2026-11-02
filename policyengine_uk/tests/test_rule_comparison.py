"""Tests for the comparison of two tax-benefit systems' rules, which decides
whether a simulation's capital gains response needs measuring at all."""

import pytest
from policyengine_core.parameters import Parameter

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.capital_gains import RESPONSE_PARAMETERS
from policyengine_uk.utils.rule_comparison import same_rules


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def test_a_copy_has_the_same_rules(system):
    assert same_rules(system, system.clone())


def test_a_value_changed_in_another_year_differs(system):
    copy = system.clone()
    copy.parameters.get_child(
        "gov.hmrc.income_tax.allowances.personal_allowance.amount"
    ).update(period="year:2030:1", value=20_000)

    assert not same_rules(system, copy)


def test_a_value_edited_in_place_differs(system):
    copy = system.clone()
    copy.parameters.get_child("gov.hmrc.cgt.basic_rate").values_list[0].value = 0.5

    assert not same_rules(system, copy)


def test_response_settings_can_be_left_out(system):
    copy = system.clone()
    copy.parameters.get_child(
        "gov.simulation.capital_gains_responses.elasticity"
    ).update(period="year:2026:1", value=2.0)

    assert not same_rules(system, copy)
    assert same_rules(system, copy, RESPONSE_PARAMETERS)


def test_an_added_parameter_differs(system):
    copy = system.clone()
    copy.parameters.get_child("gov.simulation").add_child(
        "extra", Parameter("gov.simulation.extra", {"values": {"2000-01-01": 1}})
    )

    assert not same_rules(system, copy)


def test_a_neutralised_variable_differs(system):
    copy = system.clone()
    copy.neutralize_variable("child_benefit")

    assert not same_rules(system, copy)


def test_a_replaced_formula_differs(system):
    copy = system.clone()
    # A variable with a formula: income_tax itself only adds this and the
    # winter fuel payment charge.
    formulas = copy.variables["income_tax_before_winter_fuel_payment_charge"].formulas
    formulas[next(iter(formulas))] = lambda person, period, parameters: 0

    assert not same_rules(system, copy)


def test_separately_loaded_systems_compare_as_different(system):
    """Each load holds its own copies of the variables' classes and
    formulas, so the comparison can't vouch for them: it errs towards
    measuring a response, never towards skipping one."""
    assert not same_rules(system, CountryTaxBenefitSystem())
