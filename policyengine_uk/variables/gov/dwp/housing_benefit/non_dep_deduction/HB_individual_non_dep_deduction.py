from policyengine_uk.model_api import *


class HB_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "HB_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.housing_benefit.deductions.non_dep_deduction
        weekly_income = person("total_income", period)
        deduction = p.amount.calc(weekly_income)
        return deduction * MONTHS_IN_YEAR
