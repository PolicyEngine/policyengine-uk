from policyengine_uk.model_api import *


class firm_paybill_above_auto_enrolment_upper_limit(Variable):
    value_type = float
    entity = Firm
    label = "Firm paybill of employees paid above the qualifying earnings upper limit"
    documentation = (
        "Total annual earnings of the employees counted in "
        "firm_employees_above_auto_enrolment_upper_limit. Defaults to 0."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = [
        dict(
            title="Pensions Act 2008 s.13",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/13",
        ),
    ]
