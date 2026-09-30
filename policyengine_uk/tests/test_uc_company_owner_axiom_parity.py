"""Differential test: Universal Credit reg. 77 against the Axiom encoding.

The four cases are the tests of TheAxiomFoundation/rulespec-uk
uk/regulations/uksi/2013/376/77.test.yaml (commit 0644db8), which encodes the
Universal Credit Regulations 2013 reg. 77 independently of this model. Axiom
works in monthly assessment periods; income amounts here are the monthly
figures times 12, and capital amounts are unchanged.

Axiom input -> policyengine-uk input:
- person_stands_in_position_analogous_to_sole_owner_or_partner_in_relation_to_company
  -> stands_as_sole_owner_or_partner_of_company
- company_carries_on_trade -> owned_company_carries_on_trade
- company_carries_on_property_business_within_meaning_of_corporation_tax_act_2009_section_204
  -> owned_company_carries_on_property_business
- person_derives_company_income_that_is_employed_earnings_by_itepa_part_2_chapter_8/9/10
  and intermediary_employed_earnings_derived_from_person_main_employment_activities
  -> owned_company_income_is_intermediary_employed_earnings (their conjunction)
- company_capital_value_or_person_share_value -> owned_company_capital
- company_trade_asset_value_or_person_share_used_wholly_and_exclusively_for_trade
  -> owned_company_trade_assets
- person_engaged_in_activities_in_course_of_company_trade
  -> is_engaged_in_owned_company_trade
- person_holding_value_in_company -> owned_company_holding_value
- company_income_or_person_share_calculated_as_self_employed_earnings_under_regulation_57
  -> owned_company_income_share
- person_employed_earnings_as_director_or_employee_of_company -> employment_income
- person_activities_in_course_of_company_trade_are_main_employment
  -> owned_company_is_main_employment
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2026
MONTHS = 12

CASES = {
    "trade_company_main_employment_treats_capital_income_and_mif": dict(
        inputs=dict(
            stands=True,
            trade=True,
            property=False,
            intermediary=False,
            capital=100_000,
            trade_assets=40_000,
            engaged=True,
            holding=25_000,
            income=3_000,
            director_pay=1_200,
            main=True,
        ),
        outputs=dict(
            applies=True,
            trade_assets_disregarded=40_000,
            capital=60_000,
            holding_disregarded=25_000,
            company_earnings=3_000,
            company_and_director_earnings=4_200,
            gainful=True,
            mif=True,
        ),
    ),
    "intermediary_employed_earnings_main_employment_excludes_regulation": dict(
        inputs=dict(
            stands=True,
            trade=True,
            property=False,
            intermediary=True,
            capital=100_000,
            trade_assets=40_000,
            engaged=True,
            holding=25_000,
            income=3_000,
            director_pay=1_200,
            main=True,
        ),
        outputs=dict(
            applies=False,
            trade_assets_disregarded=0,
            capital=0,
            holding_disregarded=0,
            company_earnings=0,
            company_and_director_earnings=0,
            gainful=False,
            mif=False,
        ),
    ),
    "property_business_treatment_applies_without_trade_income_rules": dict(
        inputs=dict(
            stands=True,
            trade=False,
            property=True,
            intermediary=False,
            capital=50_000,
            trade_assets=5_000,
            engaged=True,
            holding=10_000,
            income=2_000,
            director_pay=800,
            main=False,
        ),
        outputs=dict(
            applies=True,
            trade_assets_disregarded=0,
            capital=50_000,
            holding_disregarded=10_000,
            company_earnings=0,
            company_and_director_earnings=0,
            gainful=False,
            mif=False,
        ),
    ),
    "trade_assets_not_disregarded_when_person_not_engaged_in_trade_activities": dict(
        inputs=dict(
            stands=True,
            trade=True,
            property=False,
            intermediary=False,
            capital=90_000,
            trade_assets=30_000,
            engaged=False,
            holding=20_000,
            income=2_500,
            director_pay=500,
            main=False,
        ),
        outputs=dict(
            applies=True,
            trade_assets_disregarded=0,
            capital=90_000,
            holding_disregarded=20_000,
            company_earnings=2_500,
            company_and_director_earnings=3_000,
            gainful=False,
            mif=False,
        ),
    ),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_reg_77_matches_axiom(name):
    i, o = CASES[name]["inputs"], CASES[name]["outputs"]
    person = {
        "age": 40,
        "stands_as_sole_owner_or_partner_of_company": i["stands"],
        "owned_company_carries_on_trade": i["trade"],
        "owned_company_carries_on_property_business": i["property"],
        "owned_company_income_is_intermediary_employed_earnings": i["intermediary"],
        "owned_company_capital": i["capital"],
        "owned_company_trade_assets": i["trade_assets"],
        "is_engaged_in_owned_company_trade": i["engaged"],
        "owned_company_holding_value": i["holding"],
        "owned_company_income_share": i["income"] * MONTHS,
        "employment_income": i["director_pay"] * MONTHS,
        "owned_company_is_main_employment": i["main"],
    }
    sim = Simulation(
        situation={
            "people": {"p": {k: {YEAR: v} for k, v in person.items()}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )

    def calc(variable):
        return sim.calculate(variable, YEAR)[0]

    assert bool(calc("uc_company_owner_treatment_applies")) == o["applies"]
    assert calc("uc_company_capital") == pytest.approx(o["capital"])
    # Axiom's trade-asset disregard is the gap between the company capital
    # input and the capital treated as possessed, where the rule applies.
    if o["applies"]:
        assert i["capital"] - calc("uc_company_capital") == pytest.approx(
            o["trade_assets_disregarded"]
        )
    assert calc("uc_company_holding_disregard") == pytest.approx(
        o["holding_disregarded"]
    )
    assert calc("uc_company_self_employed_earnings") == pytest.approx(
        o["company_earnings"] * MONTHS
    )
    # Reg. 77(4): the company earnings are in addition to director pay.
    if o["company_and_director_earnings"]:
        assert calc("uc_company_self_employed_earnings") + calc(
            "employment_income"
        ) == pytest.approx(o["company_and_director_earnings"] * MONTHS)
    assert bool(calc("uc_company_gainful_self_employment")) == o["gainful"]
    # Axiom's minimum_income_floor_applies_due_to_company_trade is the reg.
    # 77(3)(c) trigger; the model's floor also applies to self-employment
    # income, which these cases do not have.
    assert bool(calc("uc_mif_applies")) == o["mif"]
