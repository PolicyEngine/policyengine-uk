from policyengine_uk.model_api import *


class war_widows_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "War Widow's or Widower's Pension (reported)"
    documentation = (
        "Reported War Widow's or Widower's Pension, paid under the War Pensions "
        "Scheme. In the Family Resources Survey this is benefit code 9. Rates "
        "rise each April with September CPI under the Naval, Military and Air "
        "Forces Etc. (Disablement and Death) Service Pensions (Amendment) "
        "Order, unlike Bereavement Support Payment, whose rates have been "
        "frozen since April 2017 (see bsp_reported)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2026/101/made"
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
