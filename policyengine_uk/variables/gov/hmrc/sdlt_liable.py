from policyengine_uk.model_api import *


class sdlt_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = (
        "Whether the household is liable for Stamp Duty Land Tax: it lives in "
        "England or Northern Ireland, or in Wales while HMRC charges the tax "
        "there, and the tax has not been abolished."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/48/2017-04-30"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        country = household("country", period)
        countries = country.possible_values
        in_england_or_northern_ireland = np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )
        in_wales = country == countries.WALES
        in_charged_area = in_england_or_northern_ireland | (
            in_wales & stamp_duty.applies_in_wales
        )
        return in_charged_area & (not stamp_duty.abolish)
