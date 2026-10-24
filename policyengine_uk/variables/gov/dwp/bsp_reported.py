from policyengine_uk.model_api import *


class bsp_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    documentation = (
        "Reported Bereavement Support Payment. Its rates have been frozen "
        "since April 2017 (Bereavement Support Payment Regulations 2017 reg 3, "
        "held unchanged by each up-rating order). A dataset that explicitly "
        "supplies widowed_parents_allowance_reported in the same source year "
        "declares the completed bereavement-benefit split: this input stays "
        "nominally flat, while the separate allowance and War Widow's Pension "
        "keep CPI uprating. Legacy datasets can combine Family Resources "
        "Survey benefit codes 6 and 9 here, so they retain CPI uprating, as do "
        "household situations. Unclassified amounts that the producer retains "
        "in the split BSP column also stay flat. See the dataset-source guide "
        "and #2381."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
        "https://www.legislation.gov.uk/uksi/2026/148/article/19/made",
    )
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
