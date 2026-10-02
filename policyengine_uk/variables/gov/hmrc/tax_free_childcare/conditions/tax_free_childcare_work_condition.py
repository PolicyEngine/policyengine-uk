from policyengine_uk.model_api import *


class tax_free_childcare_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "work conditions for tax-free childcare"
    documentation = (
        "The person applying and, if they have one, their partner must be "
        "in qualifying paid work, unless the partner has a qualifying "
        "disability or incapacity. Both must be at least 16. Children in the "
        "family play no part."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/28/section/3",
        "https://www.legislation.gov.uk/ukpga/2014/28/section/6",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/3",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
    )

    def formula(person, period, parameters):
        benunit = person.benunit
        # The person applying and their partner (Childcare Payments Act 2014
        # s.3(1), s.6; SI 2015/448 reg 3): the claimant or partner, aged 16+.
        applicant_or_partner = person("is_claimant_or_partner", period) & person(
            "over_16", period
        )

        treated_as_in_work = person(
            "tax_free_childcare_treated_as_in_work",
            period,
        )

        # Get disability parameters and check eligibility
        p_gc_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.child.disability
        receives_disability_programs = (
            add(
                person,
                period,
                p_gc_disability.eligibility + p_gc_disability.severe.eligibility,
            )
            > 0
        )

        has_incapacity = person("incapacity_benefit", period) > 0
        eligible_based_on_disability = receives_disability_programs | has_incapacity

        # Build conditions
        # Single adult conditions
        is_single = person.benunit("is_single", period)
        single_working = is_single & treated_as_in_work & applicant_or_partner

        # Couple conditions
        is_couple = person.benunit("is_couple", period)
        benunit_has_condition = benunit.any(
            eligible_based_on_disability & applicant_or_partner
        )
        benunit_has_worker = benunit.any(treated_as_in_work & applicant_or_partner)
        couple_both_working = is_couple & benunit.all(
            treated_as_in_work | ~applicant_or_partner
        )
        couple_one_working_one_disabled = (
            is_couple & benunit_has_worker & benunit_has_condition
        )

        return single_working | couple_both_working | couple_one_working_one_disabled
