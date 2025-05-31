from policyengine_uk.model_api import *
from numpy import ceil


class meets_marriage_allowance_income_conditions(Variable):
    label = "Meets Marriage Allowance income conditions"
    documentation = "Whether this person (and their partner) meets the conditions for this person to be eligible for the Marriage Allowance, as set out in the Income Tax Act 2007 sections 55B and 55C"
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"

    def formula(person, period):
        band = person("tax_band", period)
        bands = band.possible_values
        return (
            (band == bands.BASIC)
            | (band == bands.STARTER)
            | (band == bands.INTERMEDIATE)
        )
