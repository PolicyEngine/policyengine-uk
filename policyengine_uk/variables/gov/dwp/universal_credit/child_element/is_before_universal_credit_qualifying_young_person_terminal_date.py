from policyengine_uk.model_api import *


class is_before_universal_credit_qualifying_young_person_terminal_date(Variable):
    value_type = bool
    entity = Person
    label = "Before the Universal Credit qualifying young person terminal date"
    documentation = (
        "Whether this person is before the Universal Credit terminal date "
        "for a 19-year-old qualifying young person. This captures date-of-birth "
        "and assessment-period detail that is not otherwise available in the "
        "annual model."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.gov.uk/government/publications/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders"
