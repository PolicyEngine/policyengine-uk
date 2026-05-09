from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support rate"
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cotswold.council_tax_reduction
        weekly_income = benunit("cotswold_council_tax_reduction_weekly_income", period)
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        bands = ctr.income_band
        banded_support_rate = select(
            [
                is_couple & (num_children >= 4),
                is_couple & (num_children == 3),
                is_couple & (num_children == 2),
                is_couple & (num_children == 1),
                is_lone_parent & (num_children >= 4),
                is_lone_parent & (num_children == 3),
                is_lone_parent & (num_children == 2),
                is_lone_parent & (num_children == 1),
                is_couple,
            ],
            [
                bands.couple_four_or_more_children.calc(weekly_income_for_band),
                bands.couple_three_children.calc(weekly_income_for_band),
                bands.couple_two_children.calc(weekly_income_for_band),
                bands.couple_one_child.calc(weekly_income_for_band),
                bands.lone_parent_four_or_more_children.calc(weekly_income_for_band),
                bands.lone_parent_three_children.calc(weekly_income_for_band),
                bands.lone_parent_two_children.calc(weekly_income_for_band),
                bands.lone_parent_one_child.calc(weekly_income_for_band),
                bands.couple.calc(weekly_income_for_band),
            ],
            default=bands.single.calc(weekly_income_for_band),
        )
        passported_band_1 = (benunit("income_support", period) > 0) | (
            benunit("jsa_income", period) > 0
        )
        return where(passported_band_1, 1, banded_support_rate)
