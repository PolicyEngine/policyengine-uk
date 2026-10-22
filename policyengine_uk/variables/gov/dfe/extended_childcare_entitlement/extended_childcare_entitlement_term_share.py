from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import add_months_to_yyyymmdd, birth_day

# The model year runs from April, so its three terms begin on 1 April and
# 1 September of the year and 1 January of the next (month, day, years on).
TERM_STARTS = ((4, 1, 0), (9, 1, 0), (1, 1, 1))


class extended_childcare_entitlement_term_share(Variable):
    value_type = float
    entity = Person
    label = (
        "share of the year's terms after a child reaches the working parent minimum age"
    )
    documentation = (
        "The share of the year's three terms, beginning on 1 April and 1 "
        "September of the year and 1 January of the next, that begin after "
        "the day the child attains the minimum age for the working parent "
        "entitlement, each term a third of the year. A child is eligible "
        "from the first 1 January, 1 April or 1 September after the day its "
        "declaration has effect (SI 2022/1134 reg 27(1)(a)), which for a "
        "declaration made in advance is the day the child attains the "
        "minimum age (regs 13(2)(a), 20(a) and 25(1)); before December 2022 "
        "SI 2016/1257 reg 35(3) set the same dates from the third birthday. "
        "The day comes from date_of_birth, or from age and "
        "months_since_last_birthday, which in simulations built from data "
        "spread each single year of age over the year. So some children "
        "aged 0 in the middle of the year qualify from the autumn or spring "
        "term, and some aged 1 only from the autumn term."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/13",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/20",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/25",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/27",
        "https://www.legislation.gov.uk/uksi/2016/1257/regulation/35/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        attains_minimum_age = add_months_to_yyyymmdd(
            birth_day(person, period), 12 * p.young_child_minimum_age
        )
        year = period.start.year
        terms = sum(
            attains_minimum_age < (year + years_on) * 10_000 + month * 100 + day
            for month, day, years_on in TERM_STARTS
        )
        return terms / len(TERM_STARTS)
