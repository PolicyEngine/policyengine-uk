from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class housing_benefit_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Housing Benefit makes no non-dependant deduction for this person"
    documentation = (
        "Modelled exemptions: a full-time student (SI 2006/213 reg 74(7)(c)-(e); "
        "SI 2006/214 reg 55(7)(e)); a non-dependant on State Pension Credit "
        "(reg 74(10); reg 55(9)); and a non-dependant under 25 on Income "
        "Support or income-based JSA, or entitled to Universal Credit "
        "calculated on no earned income (reg 74(8); reg 55(8)). Not modelled: "
        "a working student's summer vacation (reg 74(7)(d)), under-25s on "
        "assessment-phase income-related ESA (no ESA group input), youth "
        "training allowances, a normal home elsewhere, and absence in hospital, "
        "prison or on armed forces operations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        full_time_student = is_full_time_student_non_dep(person, period)
        on_pension_credit = person.benunit("pension_credit", period) > 0
        on_legacy_income_related_benefit = (
            person.benunit("income_support", period) > 0
        ) | (person.benunit("jsa_income", period) > 0)
        # Entitlement before the benefit cap: universal_credit itself depends on
        # Housing Benefit through the cap.
        entitled_to_universal_credit = (
            person.benunit("universal_credit_pre_benefit_cap", period) > 0
        )
        earned_income = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        universal_credit_without_earned_income = entitled_to_universal_credit & (
            earned_income <= 0
        )
        under_age_limit = person("age", period) < p.income_related_benefit_age_limit
        return (
            full_time_student
            | on_pension_credit
            | (
                under_age_limit
                & (
                    on_legacy_income_related_benefit
                    | universal_credit_without_earned_income
                )
            )
        )
