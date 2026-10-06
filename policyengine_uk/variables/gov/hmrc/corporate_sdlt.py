from policyengine_uk.model_api import *


class corporate_sdlt(Variable):
    label = "Stamp Duty (corporations)"
    documentation = (
        "Stamp Duty paid by corporations, incident on this household. "
        "Zero when Stamp Duty Land Tax is abolished."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        if stamp_duty.abolish:
            return 0
        sd = stamp_duty.statistics
        return household("shareholding", period) * (
            sd.residential.corporate.revenue + sd.non_residential.corporate.revenue
        )
