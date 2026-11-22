from policyengine_uk.model_api import *


class firm_paybill_below_auto_enrolment_earnings_trigger(Variable):
    value_type = float
    entity = Firm
    label = (
        "Firm paybill of employees paid at or below the automatic enrolment "
        "earnings trigger"
    )
    documentation = (
        "Total annual earnings of the employees counted in "
        "firm_employees_below_auto_enrolment_earnings_trigger. Defaults to 0."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = [
        dict(
            title="Pensions Act 2008 s.3(1)(c)",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/3",
        ),
    ]
