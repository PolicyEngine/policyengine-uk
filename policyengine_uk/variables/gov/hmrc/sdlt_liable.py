from policyengine_uk.model_api import *


class sdlt_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = (
        "Whether the household is liable for Stamp Duty Land Tax: it lives in "
        "England or Northern Ireland and the tax has not been abolished."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period, parameters):
        country = household("country", period)
        countries = country.possible_values
        in_england_or_northern_ireland = np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )
        abolished = parameters(period).gov.hmrc.stamp_duty.abolish
        return in_england_or_northern_ireland & (not abolished)
