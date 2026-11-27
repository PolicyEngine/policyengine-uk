from policyengine_uk.model_api import *


class firm_employer_ni(Variable):
    label = "Firm employer National Insurance"
    documentation = (
        "Secondary Class 1 contributions the firm pays after the Employment Allowance."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.1",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/1",
        ),
    ]
    adds = ["firm_employer_ni_before_allowance"]
    subtracts = ["employment_allowance"]
