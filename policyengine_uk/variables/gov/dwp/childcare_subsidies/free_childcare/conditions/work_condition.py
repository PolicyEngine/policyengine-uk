from policyengine_uk.model_api import *


class work_eligibility_childcare(Variable):
    value_type = bool
    entity = Person
    label = "Alternative Eligibility for Free Childcare"
    documentation = "Eligibility maintained for a single parent working or receiving incapacity benefit, or a couple with one or both working."
    definition_period = YEAR

    def formula(person, period, parameters):
        """
        Calculate eligibility for free childcare based on the following conditions:
        - Single parent: working or not working but receiving incapacity benefit
        - Couple: both working or one working and one receiving incapacity benefit
        """
        # Get the benefit unit the person belongs to
        benunit = person.benunit
        is_adult = person("is_adult", period).astype(bool)

        # Check work status (in_work)
        in_work = person("in_work", period).astype(bool)

        # Check if the person is receiving incapacity benefit (simplified condition)
        has_incapacity_benefit = (
            person("incapacity_benefit", period) > 0
        ).astype(bool)

        # Build conditions for Single Parent
        is_single = (benunit.sum(is_adult) == 1).astype(bool)
        single_working = is_single & in_work
        single_not_working_but_eligible = (
            is_single & ~in_work & has_incapacity_benefit
        )

        # Build conditions for Couples
        is_couple = (benunit.sum(is_adult) == 2).astype(bool)
        couple_both_working = is_couple & benunit.all(in_work)
        couple_one_working_one_disabled = (
            is_couple
            & benunit.any(in_work)
            & benunit.any(has_incapacity_benefit)
        ).astype(bool)

        # Return eligibility for single working, single not working but eligible, couple both working, or couple one working one receiving benefit
        return (
            single_working
            | single_not_working_but_eligible
            | couple_both_working
            | couple_one_working_one_disabled
        ).astype(bool)
