from policyengine_uk.model_api import *


class widowed_parents_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Widowed Parent's Allowance (reported)"
    documentation = (
        "Reported Widowed Parent's Allowance. In the Family Resources Survey "
        "it shares benefit code 6 with Bereavement Support Payment, and "
        "datasets built so far put that code in bsp_reported. Its rates rise "
        "each April with CPI, unlike Bereavement Support Payment's, which "
        "have been frozen since April 2017 (see bsp_reported). It is closed "
        "for deaths on or after 6 April 2017; a new claim can still be made "
        "where the partner died before that date (SSCBA 1992 s.39A(1))."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2026/148/article/18/made",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/39A",
        "https://www.gov.uk/widowed-parents-allowance",
    )
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
