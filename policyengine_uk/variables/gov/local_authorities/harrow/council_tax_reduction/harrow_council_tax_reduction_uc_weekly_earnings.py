from policyengine_uk.model_api import *


class harrow_council_tax_reduction_uc_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Harrow Universal Credit CTS weekly net earnings"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        return benunit("uc_earned_income", period) / WEEKS_IN_YEAR
