from policyengine_uk.model_api import *


class wales_childcare_offer_parent_condition(Variable):
    value_type = bool
    entity = Person
    label = "meets the parent conditions for the Childcare Offer for Wales"
    documentation = (
        "Whether this parent or partner meets the Childcare Offer for Wales "
        "parent conditions (guidance paras 57 to 71 and 87). Each must have "
        "gross income of no more than £100,000 a year, and either earn on "
        "average at least 16 hours a week at their minimum wage or be "
        "enrolled in further or higher education. A parent with a caring or "
        "incapacity benefit in the exception list meets the conditions when "
        "the other parent works or studies; a lone parent cannot qualify "
        "that way. Statutory leave and the newly self-employed exemption are "
        "not modelled."
    )
    definition_period = YEAR
    defined_for = "is_claimant_or_partner"
    reference = "https://www.gov.wales/sites/default/files/publications/2026-04/childcare-offer-for-wales-guidance-for-local-authorities-april-2026-english_0.pdf"

    def formula(person, period, parameters):
        p = parameters(period).gov.welsh_government.childcare_offer

        # Paras 57 and 69: gross income of no more than £100,000, counting
        # all income, from work or investments, including statutory pay and
        # maintenance (July 2020 income guidance, questions 8 and 9).
        gross_income = add(person, period, p.income.gross_income_sources)
        within_income_limit = gross_income <= p.income.limit

        # Paras 62 to 64: employed or self-employed and earning on average at
        # least 16 hours a week at the relevant minimum wage.
        weekly_earnings = (
            add(person, period, p.income.countable_sources) / WEEKS_IN_YEAR
        )
        minimum_weekly_earnings = (
            person("minimum_wage", period) * p.income.minimum_weekly_hours
        )
        working = person("in_work", period) & (
            weekly_earnings >= minimum_weekly_earnings
        )

        # Para 71: enrolled on a further or higher education course.
        education = person("current_education", period)
        studying = np.isin(
            education.decode_to_str(), np.array(list(p.education_stages))
        )

        claimant_or_partner = person("is_claimant_or_partner", period)
        works_or_studies = (
            claimant_or_partner & (working | studying) & within_income_limit
        )

        # Para 87: a parent with a caring or incapacity benefit, whose
        # partner works or studies. A benefit-unit-level benefit in the list
        # (income-related ESA) counts for both members of a couple, as in
        # England.
        criteria = list(p.exception_criteria)
        person_criteria = [
            variable
            for variable in criteria
            if person.entity.get_variable(variable).entity.is_person
        ]
        group_criteria = [
            variable
            for variable in criteria
            if not person.entity.get_variable(variable).entity.is_person
        ]
        has_person_benefit = (
            add(person, period, person_criteria) > 0 if person_criteria else False
        )
        has_group_benefit = (
            add(person.benunit, period, group_criteria) > 0 if group_criteria else False
        )
        has_exception_benefit = has_person_benefit | has_group_benefit
        partner_works_or_studies = (
            person.benunit.sum(works_or_studies) - works_or_studies
        ) > 0
        exempt_through_partner = (
            claimant_or_partner
            & has_exception_benefit
            & partner_works_or_studies
            & within_income_limit
        )

        return works_or_studies | exempt_through_partner
