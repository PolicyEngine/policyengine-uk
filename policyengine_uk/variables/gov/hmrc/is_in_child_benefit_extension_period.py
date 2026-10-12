from policyengine_uk.model_api import *


class is_in_child_benefit_extension_period(Variable):
    value_type = bool
    entity = Person
    label = "In a Child Benefit extension period"
    documentation = (
        "Whether the person is in a Child Benefit extension period in the "
        "year: they have ceased education or training, are registered for "
        "work, education or training with a qualifying body (the Careers "
        "Service, Connexions or the Ministry of Defence), the person "
        "responsible for them was entitled to Child Benefit for them "
        "immediately before and asked for the extension within three months, "
        "and the 20 weeks from the week after they left have not run out "
        "(Child Benefit (General) Regulations 2006 reg. 5(2)(a), (b), (d), "
        "(e) and (f), and (3)). The model applies the age limit (reg. 5(1)) "
        "and the bar on remunerative work (reg. 5(2)(c)). Surveys do not "
        "record registration or the request, so this is false unless set."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2006/223/regulation/5"
