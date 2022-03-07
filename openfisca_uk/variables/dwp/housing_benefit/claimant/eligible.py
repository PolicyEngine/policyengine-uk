from openfisca_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Housing Benefit"
    documentation = "Whether this family is eligible for Housing Benefit."
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/11/made"

    def formula(benunit, period, parameters):
        return benunit("benunit_is_renting", period) & benunit("claims_legacy_benefits", period)