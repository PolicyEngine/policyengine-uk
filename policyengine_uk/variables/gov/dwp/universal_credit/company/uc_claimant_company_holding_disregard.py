from policyengine_uk.model_api import *


class uc_claimant_company_holding_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit company holdings disregarded for the claimant and partner"
    documentation = (
        "Sum of the claimant's and partner's disregarded company holdings "
        "(uc_company_holding_disregard). A dependant's holding is not theirs."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/77"

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("uc_company_holding_disregard", period)
            * benunit.members("is_uc_claimant", period)
        )
