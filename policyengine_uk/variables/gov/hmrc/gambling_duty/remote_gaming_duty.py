from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class remote_gaming_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Remote Gaming Duty"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/26/section/155",
        "https://www.legislation.gov.uk/ukpga/2026/11/section/86",
    )

    def formula_2024(household, period, parameters):
        losses = max_(household("remote_gaming_net_losses", period), 0)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.remote_gaming, period.start.year
        ):
            total += losses * rates.rate * share
        return total
