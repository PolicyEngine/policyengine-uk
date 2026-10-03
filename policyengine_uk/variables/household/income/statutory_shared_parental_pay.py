from policyengine_uk.model_api import *


class statutory_shared_parental_pay(Variable):
    label = "Statutory shared parental pay"
    documentation = (
        "Statutory shared parental pay received in the year (Social Security "
        "Contributions and Benefits Act 1992 Part 12ZC), payable for children "
        "born or placed for adoption from 5 April 2015. Employers pay it."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 171ZU (birth)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/171ZU",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 171ZV (adoption)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/171ZV",
        ),
    ]
