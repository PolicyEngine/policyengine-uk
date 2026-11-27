from policyengine_uk.model_api import *


class firm_low_paid_hours(Variable):
    value_type = float
    entity = Firm
    label = "Firm hours worked by low-paid workers"
    documentation = (
        "Annual hours worked by the firm's low-paid workers, the block whose "
        "pay firm_minimum_wage_cost compares with the adult minimum wage. "
        "firm_low_paid_paybill is the pay for these hours. Defaults to 0."
    )
    definition_period = YEAR
    hidden_input = True
    unit = "hour"
    reference = [
        dict(
            title="National Minimum Wage Act 1998 s.1",
            href="https://www.legislation.gov.uk/ukpga/1998/39/section/1",
        ),
    ]
