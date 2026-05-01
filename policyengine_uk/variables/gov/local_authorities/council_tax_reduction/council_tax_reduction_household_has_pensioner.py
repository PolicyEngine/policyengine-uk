from policyengine_uk.model_api import *


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "CTR claimant benefit unit has a pension-age member"
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        return household.any(claimant_benunit & person("is_SP_age", period))
