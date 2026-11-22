from policyengine_uk.model_api import *


class firm_employees_above_auto_enrolment_upper_limit(Variable):
    value_type = int
    entity = Firm
    label = "Firm employees paid above the qualifying earnings upper limit"
    documentation = (
        "Number of the firm's enrolled employees whose annual earnings "
        "exceed the upper limit of the qualifying earnings band, so each has "
        "qualifying earnings of the full band width. Defaults to 0."
    )
    definition_period = YEAR
    hidden_input = True
    unit = "person"
    reference = [
        dict(
            title="Pensions Act 2008 s.13",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/13",
        ),
    ]
