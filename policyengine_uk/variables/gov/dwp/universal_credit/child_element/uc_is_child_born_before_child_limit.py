from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class uc_is_child_born_before_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Born before Universal Credit child limit"
    documentation = (
        "Whether this child or qualifying young person was born before 6 April "
        "2017, so is transitionally protected from the child limit, and their "
        "responsible claimant keeps the higher child element for the first "
        "child."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/43",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.limit
        born_before_limit = birth_day(person, period) < p.born_before
        return (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            & born_before_limit
        )
