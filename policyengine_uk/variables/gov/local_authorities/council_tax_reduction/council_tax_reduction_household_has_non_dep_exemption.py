from policyengine_uk.model_api import *


class council_tax_reduction_household_has_non_dep_exemption(Variable):
    value_type = bool
    entity = Household
    label = "CTR household has a non-dependant deduction exemption"
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        claimant_or_partner = claimant_benunit & person("is_adult", period)
        is_blind = person("is_blind", period) & claimant_or_partner
        attendance_allowance = (
            person("attendance_allowance", period) > 0
        ) & claimant_or_partner
        pip_daily_living = (person("pip_dl", period) > 0) & claimant_or_partner
        dla_care = (person("dla_sc", period) > 0) & claimant_or_partner
        return household.any(
            is_blind | attendance_allowance | pip_daily_living | dla_care
        )
