from policyengine_uk.model_api import *


class housing_benefit_savings_credit_only_income(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit income for a savings-credit-only Pension Credit award"
    documentation = "Use the Pension Credit net-income assessment, with savings credit payable added and only the modifications permitted by regulation 27. The PC assessment already includes its Schedule VI earnings disregard; deduct only the additional HB amount, not both complete disregards. No HB capital tariff or general HB disability-disregard grounds replace the PC assessment. Specific partner/non-dependant attribution and war-pension inputs remain governed by their separate provisions."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )

    def formula(benunit, period, parameters):
        pc_income = benunit(
            "housing_benefit_pension_credit_net_income_assessment", period
        )
        savings_credit = benunit("pension_credit", period)
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        pc_disregard = benunit(
            "housing_benefit_pension_credit_earnings_disregard_assessment", period
        )
        hb_disregard = benunit("housing_benefit_applicable_income_disregard", period)
        modification = max_(hb_disregard - pc_disregard, 0)
        return max_(pc_income + savings_credit - childcare - modification, 0)
