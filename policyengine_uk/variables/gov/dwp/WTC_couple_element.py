from policyengine_uk.model_api import *


class WTC_couple_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit couple element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        return (relation_type == relations.COUPLE) * WTC.elements.couple
