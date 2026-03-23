from policyengine_uk.model_api import *


class council_tax_reduction_household_has_non_dep_exemption(Variable):
    value_type = bool
    entity = Household
    label = "CTR household has Dudley non-dependant deduction exemption"
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        pip_daily_living = (person("pip_dl", period) > 0) & claimant_benunit
        dla_care = (person("dla_sc", period) > 0) & claimant_benunit
        return household.any(pip_daily_living | dla_care)
