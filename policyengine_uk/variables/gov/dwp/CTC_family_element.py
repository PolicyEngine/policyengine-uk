from policyengine_uk.model_api import *


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
        ctc = parameters(period).gov.dwp.tax_credits.child_tax_credit
        person = benunit.members
        child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        age = person("age", period)
        # Tax Credits Act 2002 s.9(2)(a) and CTC Regs 2002 reg 7(2)(a), from
        # 6 April 2017: the family element is included only where the claimant
        # is responsible for a child or qualifying young person born before
        # 6 April 2017. Ages give a birth year only (birth_year is the period
        # less age), so each birthday is taken as 6 April of that year. Against
        # the 6 April 2017 cutoff that means a birth year of 2016 or earlier,
        # as the child limit reads it (is_CTC_child_limit_exempt).
        birth_year = person("birth_year", period)
        # A situation that enters birth_year for some people leaves everyone
        # else at 0; use the period less age for them.
        from_age = (period.start.year - age).astype(int)
        birth_year = where(birth_year > 0, birth_year, from_age)
        birth_date = birth_year * 10_000 + 406
        born_before_cutoff = birth_date < ctc.eligibility.family_element_born_before
        included = benunit.any(child_or_qualifying_young_person & born_before_cutoff)
        # CTC Regs 2002 reg 7(3)(a) as made, until 5 April 2011: a higher
        # family element where any child is under the age of one year.
        has_baby = benunit.any(child_or_qualifying_young_person & (age < 1))
        amount = (
            ctc.elements.family_element
            + has_baby * ctc.elements.family_element_baby_addition
        )
        return included * amount
