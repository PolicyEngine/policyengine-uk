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
        weekly_total_income = max_(person("total_income", period), 0) / WEEKS_IN_YEAR
        # Bands include their lower edge ("not less than"), as for Housing
        # Benefit (HB Regs 2006 reg 74(2)).
        return p.amount.calc(weekly_total_income) * WEEKS_IN_YEAR
