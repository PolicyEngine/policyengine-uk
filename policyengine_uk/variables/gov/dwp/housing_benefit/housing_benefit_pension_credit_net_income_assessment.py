from policyengine_uk.model_api import *


class housing_benefit_pension_credit_net_income_assessment(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Pension Credit net-income assessment supplied for Housing Benefit"
    documentation = (
        "Secretary of State's net-income assessment for a savings-credit-only "
        "award. Supply the actual assessment when known. The fallback is the "
        "model's pension_credit_income, retaining that program's coverage "
        "and limitations rather than implementing Pension Credit again in HB."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
    )

    def formula(benunit, period, parameters):
        return benunit("pension_credit_income", period)
