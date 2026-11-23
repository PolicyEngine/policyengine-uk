from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_empty_property_rates_exemption(Variable):
    value_type = float
    entity = Firm
    label = "Empty property rates exemption of the firm"
    documentation = (
        "An unoccupied property pays no rates for its first 3 months empty "
        "(6 for a qualifying industrial property), then full rates. The model "
        "treats an unoccupied property as empty throughout the year, so the "
        "exemption is gross rates times the months of the exemption period "
        "left at the start of the year (after firm_months_empty) over 12. "
        "Property with rateable value below £2,900 (from 2017-18; lower "
        "amounts before, in the parameter) "
        "is exempt for the whole year while empty (reg 4(g)). The "
        "reoccupation rule in reg 5 and the other unoccupied property "
        "exemptions (listed buildings, charity next use and others) are not "
        "modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2008/386/regulation/4"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.reliefs.empty_property
        gross = firm("firm_gross_business_rates", period)
        occupied = firm("firm_property_occupied", period)
        industrial = firm("firm_is_industrial_property", period)
        months_already_empty = firm("firm_months_empty", period)
        exemption_months = where(
            industrial, p.industrial_exempt_months, p.exempt_months
        )
        exempt_months_this_year = clip(
            exemption_months - months_already_empty, 0, MONTHS_IN_YEAR
        )
        small = firm("firm_rateable_value", period) < p.small_property_threshold
        exempt_months_this_year = where(small, MONTHS_IN_YEAR, exempt_months_this_year)
        in_england = firm("firm_rates_in_england", period)
        return where(
            occupied | ~in_england, 0, gross * exempt_months_this_year / MONTHS_IN_YEAR
        )
