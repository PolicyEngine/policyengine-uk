from policyengine_uk.model_api import *


class WTC_severely_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit severely disabled element"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/regulation/17"
    unit = GBP

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        person = benunit.members
        # The claimant, or either joint claimant, who is severely disabled
        # (reg 17); a severely disabled child counts for CTC instead.
        severely_disabled_claimants = benunit.sum(
            person("is_claimant_or_partner", period)
            & person("is_severely_disabled_for_benefits", period)
        )
        amount = severely_disabled_claimants * WTC.elements.severely_disabled
        return benunit("is_WTC_eligible", period) * amount
