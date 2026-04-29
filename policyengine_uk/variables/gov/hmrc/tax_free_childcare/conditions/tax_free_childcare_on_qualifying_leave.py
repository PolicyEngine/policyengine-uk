from policyengine_uk.model_api import *


class tax_free_childcare_on_qualifying_leave(Variable):
    value_type = bool
    entity = Person
    label = "on qualifying leave for tax-free childcare"
    documentation = (
        "Whether this person is on qualifying sickness, parenting, annual, "
        "parental bereavement, or neonatal care leave for Tax-Free Childcare."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
    ]
