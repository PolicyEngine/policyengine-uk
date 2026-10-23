from policyengine_uk.model_api import *


class bsp_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    documentation = (
        "Reported Bereavement Support Payment. Its rates have been frozen "
        "since April 2017 (Bereavement Support Payment Regulations 2017 reg 3, "
        "held unchanged by each up-rating order). Datasets built so far fill "
        "this from Family Resources Survey benefit codes 6 (Bereavement "
        "Support Payment or Widowed Parent's Allowance) and 9 (War Widow's or "
        "Widower's Pension). Code 9 is most of the value and is uprated by "
        "CPI, as is Widowed Parent's Allowance, so this variable keeps CPI "
        "uprating until datasets move code 9 into war_widows_pension_reported "
        "and Widowed Parent's Allowance into "
        "widowed_parents_allowance_reported. It should then be frozen (#2381)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2017/410/regulation/3"
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
