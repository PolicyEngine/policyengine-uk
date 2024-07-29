from policyengine_uk.model_api import *


class uc_mif_capped_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit gross earned income (incl. MIF)"
    documentation = (
        "Gross earned income for UC, with MIF applied where applicable"
    )
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
        personal_gross_earned_income = add(person, period, INCOME_COMPONENTS)
        floor = where(
            person("uc_mif_applies", period),
            person("uc_minimum_income_floor", period),
            -inf,
        )
        return max_(personal_gross_earned_income, floor)
