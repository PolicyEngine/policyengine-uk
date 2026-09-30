from policyengine_uk.model_api import *


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        weekly_income = max_(person("total_income", period), 0) / WEEKS_IN_YEAR
        # HB Regs 2006 reg 74(1)-(2): each band runs from "not less than" its
        # lower amount, so a lower edge belongs to the band above it, and a
        # non-dependant with no income pays the lowest deduction.
        deduction = p.amount.calc(weekly_income)
        return deduction * WEEKS_IN_YEAR
