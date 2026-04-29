from policyengine_uk.model_api import *


class tax_free_childcare_self_employment_start_up_period(Variable):
    value_type = bool
    entity = Person
    label = "in a self-employment start-up period for Tax-Free Childcare"
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/11"
