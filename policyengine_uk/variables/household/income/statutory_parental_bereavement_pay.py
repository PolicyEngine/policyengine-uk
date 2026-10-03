from policyengine_uk.model_api import *


class statutory_parental_bereavement_pay(Variable):
    label = "Statutory parental bereavement pay"
    documentation = (
        "Statutory parental bereavement pay received in the year (Social "
        "Security Contributions and Benefits Act 1992 Part 12ZD), payable "
        "for a child's death from 6 April 2020. Employers pay it."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992 s. 171ZZ6",
        href="https://www.legislation.gov.uk/ukpga/1992/4/section/171ZZ6",
    )
