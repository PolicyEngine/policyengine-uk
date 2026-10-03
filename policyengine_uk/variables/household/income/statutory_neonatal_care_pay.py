from policyengine_uk.model_api import *


class statutory_neonatal_care_pay(Variable):
    label = "Statutory neonatal care pay"
    documentation = (
        "Statutory neonatal care pay received in the year (Social Security "
        "Contributions and Benefits Act 1992 Part 12ZE), payable from 6 April "
        "2025 in England, Wales and Scotland. Northern Ireland has no "
        "corresponding payment. Employers pay it."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    reference = dict(
        title="Social Security Contributions and Benefits Act 1992 s. 171ZZ16",
        href="https://www.legislation.gov.uk/ukpga/1992/4/section/171ZZ16",
    )
