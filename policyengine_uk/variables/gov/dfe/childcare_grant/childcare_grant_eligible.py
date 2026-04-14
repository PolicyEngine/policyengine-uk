from policyengine_uk.model_api import *


class childcare_grant_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for Childcare Grant"
    documentation = (
        "Whether the person is eligible for Childcare Grant under the England full-time undergraduate scheme. "
        "This is a first-pass model using existing student-finance and childcare-support proxies."
    )
    definition_period = YEAR
    defined_for = "would_claim_childcare_grant"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.childcare_grant

        in_england = (
            person.household("country", period)
            == person.household("country", period).possible_values.ENGLAND
        )
        is_parent = person("is_parent", period)
        is_full_time_student = person("childcare_grant_full_time_student", period)
        student_finance_eligible = person(
            "childcare_grant_student_finance_eligible", period
        )
        receives_postgraduate_loan = person(
            "childcare_grant_receives_postgraduate_loan", period
        )
        uses_qualifying_provider = person(
            "childcare_grant_uses_qualifying_provider", period
        )

        benunit = person.benunit
        eligible_children = benunit("childcare_grant_eligible_children", period)
        household_income = person("childcare_grant_household_income", period)
        income_limit = where(
            eligible_children == 1,
            p.income_limit.one_child,
            p.income_limit.two_or_more_children,
        )

        tax_free_childcare = benunit.sum(benunit.members("tax_free_childcare", period))
        wtc_childcare = benunit("WTC_childcare_element", period)
        uc_childcare = benunit("uc_childcare_element", period)
        nhs_childcare_support = benunit.any(
            benunit.members("childcare_grant_receives_nhs_childcare_support", period)
        )

        has_incompatible_support = (
            (tax_free_childcare > 0)
            | (wtc_childcare > 0)
            | (uc_childcare > 0)
            | nhs_childcare_support
        )

        return (
            in_england
            & is_parent
            & (eligible_children > 0)
            & is_full_time_student
            & student_finance_eligible
            & ~receives_postgraduate_loan
            & (household_income < income_limit)
            & ~has_incompatible_support
            & uses_qualifying_provider
        )
