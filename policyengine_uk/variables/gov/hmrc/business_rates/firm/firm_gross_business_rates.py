from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_gross_business_rates(Variable):
    value_type = float
    entity = Firm
    label = "Gross business rates of the firm before reliefs"
    documentation = (
        "Rateable value times the business rates multiplier (the poundage in "
        "Scotland), before any relief. Modelled for England, Wales, "
        "Scotland and, from 2023-24, Northern Ireland, where it is the net "
        "annual value times the regional and district rates. The nation "
        "comes from firm_region; a firm in England also needs "
        "firm_in_england, and one in Northern Ireland "
        "firm_northern_ireland_district. Zero in Northern Ireland without a "
        "district."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/7",
        "https://www.legislation.gov.uk/ssi/2026/68/made",
        "https://www.legislation.gov.uk/nisi/1977/2157/article/6",
    ]

    def formula(firm, period, parameters):
        rateable_value = firm("firm_rateable_value", period)
        multiplier = firm("firm_business_rates_multiplier", period)
        region = firm("firm_region", period)
        regions = region.possible_values
        is_wales = region == regions.WALES
        is_scotland = region == regions.SCOTLAND
        in_england = firm("firm_rates_in_england", period)
        is_ni = firm("firm_rates_in_northern_ireland", period)
        modelled = in_england | is_wales | is_scotland | is_ni
        return where(modelled, rateable_value * multiplier, 0)
