from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_rates_in_northern_ireland(Variable):
    value_type = bool
    entity = Firm
    label = "Firm pays modelled Northern Ireland rates"
    documentation = (
        "Whether the firm's business rates follow the Northern Ireland "
        "rules: firm_region is Northern Ireland, firm_northern_ireland_district "
        "is set, and the year is 2023-24 or later, the years whose rate "
        "poundages are held."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/nisi/1977/2157/article/6"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.northern_ireland
        region = firm("firm_region", period)
        district = firm("firm_northern_ireland_district", period)
        return (
            p.modelled
            & (region == region.possible_values.NORTHERN_IRELAND)
            & (district != district.possible_values.UNKNOWN)
        )
