from policyengine_uk.model_api import *


class firm_low_paid_paybill(Variable):
    value_type = float
    entity = Firm
    label = "Firm paybill of low-paid workers"
    documentation = (
        "Pay for the hours in firm_low_paid_hours, included in firm_paybill. "
        "Defaults to 0."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = [
        dict(
            title="National Minimum Wage Act 1998 s.1",
            href="https://www.legislation.gov.uk/ukpga/1998/39/section/1",
        ),
    ]
