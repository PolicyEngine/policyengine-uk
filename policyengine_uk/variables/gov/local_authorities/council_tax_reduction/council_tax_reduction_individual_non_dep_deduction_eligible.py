from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for CTR non-dependent deduction"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9"

    def formula(person, period, parameters):
        # A boarder or lodger is liable to pay the applicant on a commercial
        # basis for their occupation, so is not a non-dependant (SI 2012/2885
        # reg 9(2)(e)).
        commercial = person("pays_rent_to_householder", period)
        return (
            (person("age", period) >= 18)
            & ~person.benunit("benunit_contains_household_head", period)
            & ~commercial
        )
