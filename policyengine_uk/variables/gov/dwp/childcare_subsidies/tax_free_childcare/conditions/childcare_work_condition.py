from policyengine_uk.model_api import *


class childcare_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for tax-free childcare"
    documentation = "Whether the person/couple meets work requirements for tax-free childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        """Calculate if person meets work conditions for:
        - Single working adult
        - Couple where either both work or one works and other has disability/incapacity
        """
        benunit = person.benunit
        is_adult = person("is_adult", period).astype(bool)

        # Basic work status
        in_work = person("in_work", period).astype(bool)

        # Get disability/incapacity conditions like we did in childcare age eligibility
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility

        is_disabled = (
            (add(person, period, standard_disability_benefits) > 0)
            | (add(person, period, severe_disability_benefits) > 0)
        ).astype(bool)

        has_incapacity = (person("incapacity_benefit", period) > 0).astype(
            bool
        )
        has_condition = (is_disabled | has_incapacity).astype(bool)

        # Build conditions
        # Single adult conditions
        is_single = (benunit.sum(is_adult) == 1).astype(bool)
        single_working = (is_single & in_work).astype(bool)

        # Couple conditions
        is_couple = (benunit.sum(is_adult) == 2).astype(bool)
        benunit_has_condition = benunit.any(has_condition)
        benunit_has_worker = benunit.any(in_work)
        couple_both_working = (is_couple & benunit.all(in_work)).astype(bool)
        couple_one_working_one_disabled = (
            is_couple & benunit_has_worker & benunit_has_condition
        ).astype(bool)

        return (
            single_working
            | couple_both_working
            | couple_one_working_one_disabled
        ).astype(bool)
