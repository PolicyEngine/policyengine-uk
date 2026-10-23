from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        income = person("council_tax_reduction_non_dep_gross_income", period)
        weekly_total_income = income / WEEKS_IN_YEAR
        return p.amount.calc(weekly_total_income, right=True) * WEEKS_IN_YEAR
