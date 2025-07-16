from policyengine_uk.model_api import *


class wtc_lone_parent_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit lone parent element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_wtc_eligible"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.working_tax_credit
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        lone_parent = family_type == families.LONE_PARENT
        return lone_parent * p.elements.lone_parent
