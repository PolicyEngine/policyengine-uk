from policyengine_uk.model_api import *


class firm_employees_below_auto_enrolment_earnings_trigger(Variable):
    value_type = int
    entity = Firm
    label = "Firm employees paid below the automatic enrolment earnings trigger"
    documentation = (
        "Number of the firm's employees whose annual earnings are below the "
        "automatic enrolment earnings trigger, so the employer need not enrol "
        "them. They are treated as not enrolled (no opt-ins). Defaults to 0, "
        "which keeps the plain average-pay approximation."
    )
    definition_period = YEAR
    hidden_input = True
    unit = "person"
    reference = [
        dict(
            title="Pensions Act 2008 s.3(1)(c)",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/3",
        ),
    ]
