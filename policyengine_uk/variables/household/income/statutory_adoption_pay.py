from policyengine_uk.model_api import *


class statutory_adoption_pay(Variable):
    label = "Statutory adoption pay"
    documentation = (
        "Statutory adoption pay received in the year (Social Security "
        "Contributions and Benefits Act 1992 Part 12ZB), payable for "
        "adoptions from 6 April 2003. Employers pay it."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992 s. 171ZL",
        href="https://www.legislation.gov.uk/ukpga/1992/4/section/171ZL",
    )
