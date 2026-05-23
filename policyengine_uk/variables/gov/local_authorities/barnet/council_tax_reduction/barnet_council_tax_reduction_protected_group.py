from policyengine_uk.model_api import *


class barnet_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Barnet CTS protected group"
    definition_period = YEAR
    reference = "https://barnet.moderngov.co.uk/documents/s94210/Appendix%20O%20-%20202627%20Council%20Tax%20Support%20Scheme.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        armed_forces_compensation = benunit.any(
            claimant_or_partner & (person("afcs", period) > 0)
        )
        war_pension = benunit(
            "barnet_council_tax_reduction_war_pension_protected", period
        )
        return benunit("benunit_contains_household_head", period) & (
            armed_forces_compensation | war_pension
        )
