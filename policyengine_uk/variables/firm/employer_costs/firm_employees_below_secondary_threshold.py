from policyengine_uk.model_api import *


class firm_employees_below_secondary_threshold(Variable):
    value_type = int
    entity = Firm
    label = "Firm employees paid below the secondary threshold"
    documentation = (
        "Number of the firm's employees whose Class 1 earnings for the year "
        "are at or below the annual secondary threshold, so pay no secondary "
        "contributions. Used with their pay to remove them from the "
        "average-pay approximation of earnings above the threshold. Defaults "
        "to 0, which keeps the plain average-pay approximation."
    )
    definition_period = YEAR
    hidden_input = True
    unit = "person"
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        ),
    ]
