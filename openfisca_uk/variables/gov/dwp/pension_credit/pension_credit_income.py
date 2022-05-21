from openfisca_uk.model_api import *


class pension_credit_income(Variable):
    label = "Income for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/15"

    def formula(benunit, period, parameters):
        sources = parameters(period).dwp.pension_credit.guarantee_credit.income
        total = add(benunit, period, sources)
        bi = parameters(period).contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            total += add(benunit, period, ["basic_income"])
        return max_(0, total)
