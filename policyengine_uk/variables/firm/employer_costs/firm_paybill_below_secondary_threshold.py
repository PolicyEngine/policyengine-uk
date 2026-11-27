from policyengine_uk.model_api import *


class firm_paybill_below_secondary_threshold(Variable):
    value_type = float
    entity = Firm
    label = "Firm paybill of employees paid at or below the secondary threshold"
    documentation = (
        "Total Class 1 earnings for the year of the employees counted in "
        "firm_employees_below_secondary_threshold. Defaults to 0."
        " Measure the split at the simulated year's secondary threshold "
        "(£9,100 in 2022-23 to 2024-25, £5,000 from 2025-26); with a split "
        "measured at another threshold, or a reform to the threshold, the "
        "base is approximate."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        ),
    ]
