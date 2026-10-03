from policyengine_uk.model_api import *


class uc_mif_capped_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit gross earned income (incl. MIF)"
    documentation = "Gross earned income for UC, with MIF applied where applicable"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        # UC Regs 2013 reg 57(2) Steps 1-2 add together the profit or loss of
        # each of the person's trades, and Step 3 makes a negative total nil:
        # one trade's loss reduces another trade's profits but never employed
        # earnings. Over a year with both spread evenly, the loss offsets
        # profits up to their amount.
        losses_set_against_profits = min_(
            person("trading_loss", period), person("self_employment_income", period)
        )
        personal_gross_earned_income = (
            add(person, period, INCOME_COMPONENTS) - losses_set_against_profits
        )
        floor = where(
            person("uc_mif_applies", period),
            person("uc_minimum_income_floor", period),
            -inf,
        )
        return max_(personal_gross_earned_income, floor)
