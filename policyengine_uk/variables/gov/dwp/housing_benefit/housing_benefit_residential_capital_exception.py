from policyengine_uk.model_api import *


class housing_benefit_residential_capital_exception(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit residential capital tariff exception"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Pre-assessed qualification for the working-age residential capital "
        "tariff exception: GB HB regulation 52(4)-(5), (8)-(9), or NI "
        "regulation 49(3)-(4), (7)-(8). This includes the specified historical "
        "saved circumstances; generic supported housing, a care-home label "
        "or in_specified_or_temporary_accommodation does not establish it. "
        "Supply true only after assessing the applicable jurisdiction's rules. "
        "No dataset mapping has been verified. Missing input defaults to false "
        "and retains the ordinary threshold; that approximation may understate "
        "Housing Benefit for qualifying residents. This does not change "
        "eligibility, capital ownership/valuation or the upper capital limit."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/52",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/49",
    )
