from policyengine_uk.model_api import *


class is_non_exempt_adult_resident_for_pension_credit_severe_disability(Variable):
    value_type = bool
    entity = Person
    label = "Adult whose residence bars the Pension Credit severe disability addition"
    documentation = (
        "Whether this person has attained 18 and is not a person whose "
        "presence SPC Regs 2002 Sch. I para. 2 ignores. Someone like this "
        "normally residing with a claimant or partner, other than that "
        "claimant or partner themselves, bars the severe disability addition "
        "(Sch. I para. 1(1)(a)(ii), (b)(ii), (c)(iii))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.severe_disability
        adult = person("age", period) >= p.resident_age_limit
        ignored = (
            # Para. 2(2)(a).
            person(
                "receives_pension_credit_severe_disability_qualifying_benefit", period
            )
            # Para. 2(2)(b).
            | person("is_blind", period)
            # Para. 2(2)(f): a child is under 16, so below the age limit; a
            # qualifying young person may be 18 or 19.
            | person("is_qualifying_young_person_for_pension_credit", period)
            # Para. 2(2)(c)-(e), (3)-(7) and para. 3(1).
            | person("is_ignored_resident_for_pension_credit_severe_disability", period)
        )
        return adult & ~ignored
