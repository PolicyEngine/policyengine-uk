from policyengine_uk.model_api import *


class tax_free_childcare_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "work conditions for tax-free childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        is_adult = person("is_adult", period)

        # Basic work status
        in_work = person("in_work", period)

        # Get disability parameters and check eligibility
        p_gc_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.child.disability
        receives_disability_programs = (
            add(
                person,
                period,
                p_gc_disability.eligibility
                + p_gc_disability.severe.eligibility,
            )
            > 0
        )

        has_incapacity = person("incapacity_benefit", period) > 0
        eligible_based_on_disability = (
            receives_disability_programs | has_incapacity
        )

        # Build conditions
        # Single adult conditions
        is_single = person.benunit("is_single", period)
        single_working = is_single & in_work

        # Couple conditions
        is_couple = person.benunit("is_couple", period)
        benunit_has_condition = benunit.any(
            eligible_based_on_disability & is_adult
        )
        benunit_has_worker = benunit.any(in_work & is_adult)
        couple_both_working = is_couple & benunit.all(
            in_work | ~person("is_parent", period)
        )
        couple_one_working_one_disabled = (
            is_couple & benunit_has_worker & benunit_has_condition
        )

        return (
            single_working
            | couple_both_working
            | couple_one_working_one_disabled
        )
