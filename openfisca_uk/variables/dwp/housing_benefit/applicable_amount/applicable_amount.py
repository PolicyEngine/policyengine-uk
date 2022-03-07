from openfisca_uk.model_api import *


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "HB applicable amount"
    documentation = "The total income disregard for Housing Benefit."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/made"

    def formula(benunit, period, parameters):
        HB = parameters(period).dwp.housing_benefit
        PA = HB.allowances
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_adult_age", period)
        personal_allowance = benunit("hb_personal_allowance", period)
        premiums = benunit("benefits_premiums", period)
        housing_benefit_eligible = benunit("housing_benefit_eligible", period)
        return (personal_allowance + premiums) * housing_benefit_eligible
