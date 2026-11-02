from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class cash_isa_subscription_limit(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA subscription limit for the person"
    documentation = (
        "The most the person can subscribe to cash ISAs in the tax year: the "
        "cash ISA subscription limit while they are under the full limit age "
        "at the end of the year, and otherwise the annual subscription limit, "
        "which also caps the cash limit. Current law sets no cash limit of its "
        "own, so this is the annual limit unless a reform sets one. The age at "
        "the end of the year (5 April) comes from the date of birth, so a "
        "person aged 64 on 6 October whose 65th birthday falls by 5 April has "
        "the annual limit."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.isa
        # Reg 4ZA(1ZA) applies to a person who is 64 or under at the end of
        # the year, 5 April. A person attains an age at the start of their
        # birthday, so they have reached the full-limit age by then if they
        # were born before 6 April that many years before the year ends.
        born_before = (period.start.year + 1 - p.cash.full_limit_age) * 10_000 + 406
        reached_full_limit_age = birth_day(person, period) < born_before
        cash_limit = where(reached_full_limit_age, np.inf, p.cash.subscription_limit)
        return min_(cash_limit, p.annual_subscription_limit)
