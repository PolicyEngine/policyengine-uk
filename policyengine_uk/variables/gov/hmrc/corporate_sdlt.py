from policyengine_uk.model_api import *


class corporate_sdlt(Variable):
    label = "Stamp Duty (corporations)"
    documentation = (
        "Stamp Duty paid by corporations, incident on this household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        sd = parameters(period).gov.hmrc.stamp_duty.statistics
        return household("shareholding", period) * (
            sd.residential.corporate.revenue
            + sd.non_residential.corporate.revenue
        )
