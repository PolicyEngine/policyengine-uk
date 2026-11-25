from policyengine_uk.model_api import *


class sdlt_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = (
        "Whether the household is liable for Stamp Duty Land Tax: it lives in "
        "England or Northern Ireland, or in Wales or Scotland while HMRC "
        "charges the tax there, and no reform sets "
        "gov.hmrc.stamp_duty.abolish."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/14/section/48/enacted",
        "https://www.legislation.gov.uk/ukpga/2012/11/section/29",
        "https://www.legislation.gov.uk/uksi/2015/637/article/2/made",
    )

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        country = household("country", period)
        countries = country.possible_values
        in_england_or_northern_ireland = np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )
        in_wales = country == countries.WALES
        in_scotland = country == countries.SCOTLAND
        in_charged_area = (
            in_england_or_northern_ireland
            | (in_wales & stamp_duty.applies_in_wales)
            | (in_scotland & stamp_duty.applies_in_scotland)
        )
        return in_charged_area & (not stamp_duty.abolish)
