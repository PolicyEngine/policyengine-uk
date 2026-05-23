from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_full_support_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "West Northamptonshire CTR 100 percent support group"
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        care_leaver_under_25 = benunit.any(
            claimant_or_partner
            & (person("age", period) <= 25)
            & person("west_northamptonshire_council_tax_reduction_care_leaver", period)
        )
        war_pension = benunit(
            "west_northamptonshire_council_tax_reduction_war_pension_protected",
            period,
        )
        return care_leaver_under_25 | war_pension
