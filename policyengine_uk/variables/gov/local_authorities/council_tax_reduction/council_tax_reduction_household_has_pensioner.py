from policyengine_uk.model_api import *


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "CTR claimant benefit unit is a pensioner"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3"

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        pensioner = person.benunit("council_tax_reduction_pensioner", period)
        return household.any(claimant_benunit & pensioner)
