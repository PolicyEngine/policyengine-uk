from policyengine_uk.model_api import *


class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = "Blind Person's Allowance for the year (not simulated)"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"
    unit = GBP
