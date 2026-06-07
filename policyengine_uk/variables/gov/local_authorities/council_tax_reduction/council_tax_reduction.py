from policyengine_uk.model_api import *


class council_tax_reduction(Variable):
    value_type = float
    entity = Household
    label = "Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        person = household.members
        return household.sum(
            person.benunit("council_tax_benefit", period)
            * person("is_benunit_head", period)
        )
