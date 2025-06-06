from policyengine_uk.model_api import *


class council_tax_less_benefit(Variable):
    label = "Council Tax (less CTB)"
    documentation = "Council Tax minus the Council Tax Benefit"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        person = household.members
        council_tax_benefit = household.sum(
            person.benunit("council_tax_benefit", period)
            * person("is_benunit_head", period)
        )
        return household("council_tax", period) - council_tax_benefit
