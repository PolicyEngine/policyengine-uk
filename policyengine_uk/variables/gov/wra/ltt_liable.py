from policyengine_uk.model_api import *


class ltt_liable(Variable):
    label = "Liable for Land Transaction Tax"
    documentation = (
        "Whether the household is liable to pay the Wales Land Transaction "
        "Tax: it lives in Wales and HMRC no longer charges Stamp Duty Land "
        "Tax there."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    reference = [
        # Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales)
        # Act 2017 s. 2, in force from 1 April 2018 under WSI 2018/34 art. 3.
        "https://www.legislation.gov.uk/anaw/2017/1/section/2",
        "https://www.legislation.gov.uk/wsi/2018/34/article/3/made",
    ]

    def formula(household, period, parameters):
        country = household("country", period)
        in_wales = country == country.possible_values.WALES
        sdlt_applies_in_wales = parameters(period).gov.hmrc.stamp_duty.applies_in_wales
        return in_wales & (not sdlt_applies_in_wales)
