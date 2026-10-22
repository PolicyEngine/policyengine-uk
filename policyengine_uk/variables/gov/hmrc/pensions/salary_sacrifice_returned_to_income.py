from policyengine_uk.model_api import *


class salary_sacrifice_returned_to_income(Variable):
    """Legacy supplied input, defaulting to zero; never computed by the model."""

    label = "Salary sacrifice actually returned to ordinary income"
    documentation = (
        "Legacy ordinary-pay/member-payment input, defaulting to zero. The "
        "pension salary-sacrifice cap changes only NIC earnings, through "
        "salary_sacrifice_pension_ni_excess; it does not return cash pay or "
        "create a member contribution. Explicit inputs remain supported for "
        "callers representing an actual return to ordinary pay and member "
        "payments under the existing input convention."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    default_value = 0
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/section/308"
