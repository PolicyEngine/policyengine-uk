from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class CTC_family_element(Variable):
    value_type = float
    entity = BenUnit
    label = "CTC entitlement in the Family Element"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/2002/21/section/9",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7",
    ]
    unit = GBP
    defined_for = "is_CTC_eligible"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit
        if not p.eligibility.family_element_birth_date_condition_applies:
            return p.elements.family_element

        person = benunit.members
        qualifying_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        born_before = (
            birth_day(person, period) < p.eligibility.family_element_born_before
        )
        return p.elements.family_element * benunit.any(qualifying_child & born_before)
