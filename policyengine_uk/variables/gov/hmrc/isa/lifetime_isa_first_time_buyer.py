from policyengine_uk.model_api import *


class lifetime_isa_first_time_buyer(Variable):
    value_type = bool
    entity = Person
    label = "First-time buyer for Lifetime ISA purposes"
    documentation = "Whether this investor has never owned a residential property or equivalent interest anywhere, under paragraph 7 of the Lifetime ISA rules. This is the investor's status; another joint buyer may previously have owned property."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/7"
