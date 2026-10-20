from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        # Other investment income is left out of the band for now, as in
        # household_benefits_individual_non_dep_deduction: the bands apply only
        # to a non-dependant in remunerative work (SI 2012/2885 Sch 1 para
        # 8(2)), which this formula does not yet test (#2007).
        income = person("total_income", period) - person(
            "other_investment_income", period
        )
        weekly_total_income = income / WEEKS_IN_YEAR
        return p.amount.calc(weekly_total_income, right=True) * WEEKS_IN_YEAR
