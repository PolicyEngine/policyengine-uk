from policyengine_uk.model_api import *


class income_support_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount of Income Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2"

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        amounts = IS.amounts
        younger_age = benunit("youngest_claimant_or_partner_age", period)
        older_age = benunit("eldest_claimant_or_partner_age", period)
        younger_under_18 = younger_age < amounts.age_threshold.younger
        younger_under_25 = younger_age < amounts.age_threshold.older
        older_under_18 = older_age < amounts.age_threshold.younger
        has_children = benunit(
            "is_responsible_for_child_or_young_person_for_legacy_benefits", period
        )
        single = benunit("is_single", period)
        single_under_25 = single & ~has_children & younger_under_25
        single_over_25 = single & ~has_children & ~younger_under_25
        lone_young = single & has_children & younger_under_18
        lone_old = single & has_children & ~younger_under_18
        couple_young = ~single & older_under_18
        couple_mixed = ~single & ~older_under_18 & younger_under_18
        couple_old = ~single & ~younger_under_18
        # Retain the existing simplified couple rates. Schedule 2 para 1(3)
        # has higher child/own-right qualification branches (a), (e), and a
        # lower rate for an 18-24 claimant with an under-18 partner (f).
        # Those distinctions require a separate allowance-policy change.
        personal_allowance_weekly = select(
            [
                single_under_25,
                single_over_25,
                lone_young,
                lone_old,
                couple_young,
                couple_mixed,
                couple_old,
            ],
            [
                amounts.amount_16_24,
                amounts.amount_over_25,
                amounts.amount_lone_16_17,
                amounts.amount_lone_over_18,
                amounts.amount_couples_16_17,
                amounts.amount_couples_age_gap,
                amounts.amount_couples_over_18,
            ],
        )
        personal_allowance = personal_allowance_weekly * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
