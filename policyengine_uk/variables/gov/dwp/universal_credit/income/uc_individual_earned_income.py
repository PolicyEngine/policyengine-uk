from policyengine_uk.model_api import *


class uc_individual_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit earned income of the person"
    documentation = (
        "The person's earned income for Universal Credit before the work "
        "allowance: their earnings less their own pension contributions, "
        "income tax and National Insurance, or the amount the minimum income "
        "floor treats them as having where that applies."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 62(2) and (3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
    ]

    def formula(person, period, parameters):
        earned_income = person("uc_individual_earned_income_before_mif", period)
        # Reg. 62 compares earned income, after the deductions, with the
        # net threshold. A single claimant below their threshold is treated
        # as having the threshold (reg. 62(2)). A member of a couple is
        # treated as having it only while the couple's combined earned
        # income is also below the couple threshold, less any amount by
        # which it and the partner's earned income would exceed that
        # threshold (reg. 62(3)). The couple threshold is the sum of the
        # joint claimants' individual thresholds (reg. 90(3)(a)); for a
        # single claimant it is their own, and reg. 62(3) reduces to
        # reg. 62(2). Partners' earned income is their actual earned income:
        # when both are below their thresholds each is treated as having
        # their own, whichever partner's floor is applied first. A claim has
        # at most two claimants; where the data flag more (an adult child in
        # the parents' benefit unit), the two eldest are the couple.
        age = person("age", period)
        is_claimant = person("is_uc_claimant", period)
        claimant = is_claimant & (
            person.get_rank(person.benunit, -age, condition=is_claimant) < 2
        )
        claimant_earned_income = earned_income * claimant
        partner_earned_income = (
            person.benunit.sum(claimant_earned_income) - claimant_earned_income
        )
        individual_threshold = person("uc_minimum_income_floor", period)
        couple_threshold = person.benunit.sum(individual_threshold * claimant)
        below_individual_threshold = earned_income < individual_threshold
        below_couple_threshold = (
            earned_income + partner_earned_income < couple_threshold
        )
        floor = individual_threshold - max_(
            0, individual_threshold + partner_earned_income - couple_threshold
        )
        floor_applies = (
            person("uc_mif_applies", period)
            & claimant
            & below_individual_threshold
            & below_couple_threshold
        )
        return where(floor_applies, floor, earned_income)
