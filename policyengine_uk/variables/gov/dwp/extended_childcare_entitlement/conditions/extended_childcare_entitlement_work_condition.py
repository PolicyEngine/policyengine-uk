from policyengine_uk.model_api import *


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for extended childcare entitlement"
    documentation = "Whether the person/couple meets work requirements for extended childcare entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        is_adult = person("is_adult", period)

        # Basic work status
        in_work = person("in_work", period).astype(bool)

        # Get disability/incapacity conditions like we did in childcare age eligibility
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility

        receive_disability_program = (
            (add(person, period, standard_disability_benefits) > 0)
            | (add(person, period, severe_disability_benefits) > 0)
        ).astype(bool)

        has_incapacity = (person("incapacity_benefit", period) > 0).astype(
            bool
        )
        eligible_based_on_disability = (
            receive_disability_program | has_incapacity
        ).astype(bool)

        # Build conditions
        # Single adult conditions
        is_single = person.benunit("is_single", period)
        single_working = (is_single & in_work).astype(bool)

        # Couple conditions
        is_couple = person.benunit("is_couple", period)
        benunit_has_condition = benunit.any(eligible_based_on_disability)
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
