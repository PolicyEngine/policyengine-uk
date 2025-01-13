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
        is_adult = person("is_adult", period)

        # Basic work status
        in_work = person("in_work", period)

        # Get disability/incapacity conditions like we did in childcare age eligibility
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility

        is_disabled = (
            add(person, period, standard_disability_benefits)
            | add(person, period, severe_disability_benefits)
        ) > 0

        has_incapacity = person("incapacity_benefit", period) > 0

        # Build conditions
        # Single adult conditions
        is_single = benunit.sum(is_adult) == 1
        single_working = is_single & in_work

        # Couple conditions
        is_couple = benunit.sum(is_adult) == 2
        partner_in_work = in_work
        partner_has_condition = is_disabled | has_incapacity

        couple_both_working = is_couple & in_work & partner_in_work
        is_partner_working_with_disabled_person = (
            is_couple & partner_in_work & (is_disabled | has_incapacity)
        )
        is_person_working_with_disabled_partner = (
            is_couple & in_work & partner_has_condition
        )

        return (
            single_working
            | couple_both_working
            | is_person_working_with_disabled_partner
            | is_partner_working_with_disabled_person
        )
