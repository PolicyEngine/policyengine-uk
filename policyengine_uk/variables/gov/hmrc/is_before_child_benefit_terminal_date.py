from policyengine_uk.model_api import *


class is_before_child_benefit_terminal_date(Variable):
    value_type = bool
    entity = Person
    label = "Before the Child Benefit terminal date after leaving education"
    documentation = (
        "Whether, for some of the year, the person has left relevant "
        "education or approved training and the week that includes their "
        "terminal date has not ended. The terminal date is the last day of "
        "February, May, August or November, whichever comes first after they "
        "left, or after their last external examination if they were entered "
        "for one (Child Benefit (General) Regulations 2006 reg. 7(2), Cases 1 "
        "and 2). The model holds one education status for the year and no "
        "leaving date, so this is false unless set."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2006/223/regulation/7"
