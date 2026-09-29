from policyengine_uk.model_api import *


class is_before_first_september_after_19th_birthday(Variable):
    value_type = bool
    entity = Person
    label = "Before the 1 September following their 19th birthday"
    documentation = (
        "Whether it is not yet the 1 September following this person's 19th "
        "birthday. That date ends qualifying young person status in education "
        "or training for both Pension Credit (SPC Regs 2002 reg 4A(1)(b)) and "
        "Universal Credit (UC Regs 2013 reg 5(1)(b)). The annual model holds "
        "age in whole years and no date of birth, so this is an input. Until "
        "a dataset writes this column, it reads the Universal Credit-named "
        "input is_before_universal_credit_qualifying_young_person_terminal_date, "
        "which defaults to false."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(person, period, parameters):
        return person(
            "is_before_universal_credit_qualifying_young_person_terminal_date",
            period,
        )
