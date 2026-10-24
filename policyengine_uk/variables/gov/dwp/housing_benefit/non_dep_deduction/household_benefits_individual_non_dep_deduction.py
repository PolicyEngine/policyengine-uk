from policyengine_uk.model_api import *


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        # Other investment income is left out of the band for now. These bands
        # apply only to a non-dependant in remunerative work (HB Regs 2006 reg
        # 74(2); SPC Regs reg 55(2)), and the model does not yet test that, so
        # counting it would band non-workers whose only income is investment
        # income. #2007 implements reg 74 in full and can then include it.
        # Spousal maintenance is tax-exempt, but is normal gross income and
        # has no disregard under reg 74(9) or pension-age reg 55(10).
        income = (
            person("total_income", period)
            - person("other_investment_income", period)
            + max_(0, person("spousal_maintenance_income", period))
        )
        weekly_income = income / WEEKS_IN_YEAR
        deduction = p.amount.calc(weekly_income, right=True)
        return deduction * WEEKS_IN_YEAR
