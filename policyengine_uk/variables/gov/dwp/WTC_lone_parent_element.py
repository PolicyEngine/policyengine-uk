from policyengine_uk.model_api import *


class WTC_lone_parent_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit lone parent element"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/regulation/12"
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        # A single claim by a claimant responsible for a child or qualifying
        # young person (reg 12).
        lone_parent = benunit("is_single", period) & benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_child_tax_credit",
            period,
        )
        return lone_parent * WTC.elements.lone_parent
