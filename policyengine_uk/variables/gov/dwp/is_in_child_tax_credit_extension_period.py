from policyengine_uk.model_api import *


class is_in_child_tax_credit_extension_period(Variable):
    value_type = bool
    entity = Person
    label = "In a Child Tax Credit extension period"
    documentation = (
        "Whether, for some of the year, the person has ceased full-time "
        "education or approved training, HMRC was notified within three "
        "months that they are registered for work or training with a "
        "qualifying body (the Careers Service, Connexions or the Ministry of "
        "Defence), and no more than 20 weeks have passed since they left "
        "(Child Tax Credit Regulations 2002 reg. 5(3)(b)(i)-(iii)). The model "
        "applies the age limit (reg. 5(3)(b)) and the second condition (reg. "
        "5(4)). Surveys do not record the registration, so this is false "
        "unless set."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5"
