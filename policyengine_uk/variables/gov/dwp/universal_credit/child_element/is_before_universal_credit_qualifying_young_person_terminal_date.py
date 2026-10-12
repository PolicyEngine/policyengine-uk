from policyengine_uk.model_api import *


class is_before_universal_credit_qualifying_young_person_terminal_date(Variable):
    value_type = bool
    entity = Person
    label = "Before the Universal Credit qualifying young person terminal date"
    documentation = (
        "Whether this person is before the Universal Credit terminal date for "
        "a 19-year-old qualifying young person: the 1 September following "
        "their 19th birthday (UC Regs 2013 reg. 5(1)(b)). It follows the date "
        "of birth (is_before_first_september_following_19th_birthday), so a "
        "year counts if it starts before that date. Datasets and situations "
        "can set it directly: set it to false for a 19-year-old whose 1 "
        "September has passed. Its default is true, the value the date fact "
        "gives everyone under 20 on 6 October, so setting it for some people "
        "leaves everyone else under 20 where the date fact puts them; older "
        "people are excluded by the age limit before it is read."
    )
    definition_period = YEAR
    default_value = True
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.gov.uk/government/publications/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders",
    )

    def formula(person, period, parameters):
        return person("is_before_first_september_following_19th_birthday", period)
