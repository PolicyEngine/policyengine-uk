from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_childcare_disabled_partner(Variable):
    value_type = bool
    entity = Person
    label = "Cheltenham Council Tax Support source childcare disabled partner flag"
    definition_period = YEAR
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"
    default_value = False
