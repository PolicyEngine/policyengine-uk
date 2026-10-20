from policyengine_uk.model_api import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    documentation = (
        "Receives or is entitled to a carer benefit, or provides at least the "
        "Carer's Allowance qualifying hours of care a week. The Universal "
        "Credit carer element does not require a Carer's Allowance claim. "
        "Entitlement-based additions and premiums use "
        "is_entitled_to_carer_benefit; receipt-based rules use "
        "receives_carer_benefit. A "
        "carer whose allowance is reduced to nil by an overlapping benefit, "
        "such as State Pension, stays entitled. The hours limb tests "
        "hours alone, as carers_allowance_pre_overlap does: it does not check that the "
        "person cared for receives a qualifying disability benefit (part of "
        "the Carer's Allowance conditions referenced by regulation 30), so a "
        "survey hours field counts caring for "
        "anyone and a dataset's take-up input carries that simplification. "
        "A reported Carer's Allowance award the person would claim also "
        "counts, so a carer whose earnings put them over the Carer's Allowance "
        "earnings limit keeps the Universal Credit carer element, which does "
        "not apply that limit (regulation 30(1)(a)(i))."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/30"

    def formula(person, period, parameters):
        min_hours = parameters(period).gov.dwp.carers_allowance.min_hours
        meets_hours = person("care_hours", period) >= min_hours
        # A reported Carer's Allowance award the person would claim is
        # evidence of the caring itself, where no hours are recorded. It still
        # counts when the earnings limit (which the Universal Credit carer
        # element does not apply) stops the allowance being paid. Requiring
        # would_claim is a modelling convention, not the law: regulation 30(2)
        # applies whether or not a claim is made. It keeps an award the person
        # would not claim counting no more than it did before; in the data,
        # would_claim follows reported receipt.
        reports_carers_allowance = (
            person("carers_allowance_reported", period) > 0
        ) & person("would_claim_carers_allowance", period)
        return (
            person("receives_carer_benefit", period)
            | person("is_entitled_to_carer_benefit", period)
            | meets_hours
            | reports_carers_allowance
        )
