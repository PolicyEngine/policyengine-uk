from policyengine_uk.model_api import *


class legacy_prescribed_accommodation_capital_exception(Variable):
    value_type = bool
    entity = BenUnit
    label = "Legacy benefit prescribed accommodation capital tariff exception"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Pre-assessed qualification for the higher capital tariff threshold of "
        "Income Support, income-based JSA and income-related ESA: the claimant "
        "lives permanently in prescribed accommodation (GB: IS Regs 1987 reg "
        "53(1B)-(1C), JSA Regs 1996 reg 116(1B)-(1C), ESA Regs 2008 reg "
        "118(3)-(4); NI: the same regulations of the Northern Ireland rules). "
        "In Great Britain that is a care home, an independent hospital, an "
        "Abbeyfield Home, or Polish Resettlement Act accommodation where the "
        "claimant needs and receives personal care; in Northern Ireland it is a "
        "residential care home, a nursing home, an independent hospital or an "
        "Abbeyfield Home. That includes the absences each regulation treats as "
        "living there permanently. Supply true only after assessing the "
        "applicable jurisdiction's rules. Housing Benefit prescribes different "
        "circumstances (housing_benefit_residential_capital_exception), and "
        "neither input sets the other. Other members who claim in their own "
        "right share the benefit unit's tariff income under the existing "
        "proxy. No dataset supplies this input. Missing input defaults to "
        "false and retains the ordinary threshold; that approximation may "
        "understate these benefits for qualifying residents. This does not "
        "change eligibility, capital ownership/valuation or the upper capital "
        "limit."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/53",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/116",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/118",
        "https://www.legislation.gov.uk/nisr/1996/93/regulation/11/made",
        "https://www.legislation.gov.uk/nisr/1996/356/regulation/10/made",
        "https://www.legislation.gov.uk/nisr/2005/458/schedule/1/made",
        "https://www.legislation.gov.uk/nisr/2005/458/schedule/3/made",
        "https://www.legislation.gov.uk/nisr/2008/280/regulation/118",
    )
