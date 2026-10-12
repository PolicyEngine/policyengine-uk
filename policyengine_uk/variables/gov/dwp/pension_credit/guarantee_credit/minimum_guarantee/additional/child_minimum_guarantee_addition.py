from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class child_minimum_guarantee_addition(Variable):
    label = "Child-related addition"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA"

    def formula(benunit, period, parameters):
        person = benunit.members
        is_child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_pension_credit", period
        )
        # Sch IIA para 10: the eldest child or qualifying young person, by date
        # of birth, gets the first child amount if born before 6 April 2017.
        date_of_birth = birth_day(person, period)
        child_index = (
            person.get_rank(
                person.benunit,
                date_of_birth,
                condition=is_child_or_qualifying_young_person,
            )
            + 1
        )
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        first_child_born_before_cutoff = (child_index == 1) & (
            date_of_birth < gc.child.first.born_before
        )
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility
        is_disabled = add(person, period, standard_disability_benefits) > 0
        is_severely_disabled = add(person, period, severe_disability_benefits) > 0
        is_standard_disabled = is_disabled & ~is_severely_disabled
        is_not_disabled = ~is_disabled
        child_addition = where(
            first_child_born_before_cutoff,
            gc.child.first.addition,
            gc.child.addition,
        )
        per_child_amount = (
            select(
                [
                    is_child_or_qualifying_young_person & is_not_disabled,
                    is_child_or_qualifying_young_person & is_standard_disabled,
                    is_child_or_qualifying_young_person & is_severely_disabled,
                ],
                [
                    child_addition,
                    child_addition + gc.child.disability.addition,
                    child_addition + gc.child.disability.severe.addition,
                ],
            )
            * WEEKS_IN_YEAR
        )
        return benunit.sum(per_child_amount)
