from policyengine_uk.model_api import *


class lbtt_liable(Variable):
    label = "Liable for Land and Buildings Transaction Tax"
    documentation = (
        "Whether the household is liable for Land and Buildings Transaction "
        "Tax: it lives in Scotland and the tax is in effect."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/11/section/28",
        "https://www.legislation.gov.uk/ssi/2015/108/article/2/made",
    )

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        if not lbtt.in_effect:
            return household.filled_array(False)

        country = household("country", period)
        countries = country.possible_values
        return country == countries.SCOTLAND
