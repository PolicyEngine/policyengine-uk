from policyengine_uk.model_api import *


class tax_free_childcare_on_shared_parental_leave(Variable):
    value_type = bool
    entity = Person
    label = "on shared parental leave for tax-free childcare"
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/12"
