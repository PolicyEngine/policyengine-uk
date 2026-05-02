from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.plymouth.council_tax_reduction
        weekly_income = benunit("plymouth_council_tax_reduction_weekly_income", period)
        income_bands = ctr.income_band
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        has_child_under_5 = benunit.any(
            child_or_young_person & (person("age", period) < 5)
        )
        war_pensioner = benunit("plymouth_council_tax_reduction_war_pensioner", period)
        is_couple = benunit("is_couple", period)
        banded_support_rate = select(
            [
                war_pensioner,
                has_child_under_5,
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                income_bands.war_pensioner.calc(weekly_income_for_band),
                income_bands.child_under_5.calc(weekly_income_for_band),
                income_bands.two_or_more_children.calc(weekly_income_for_band),
                income_bands.one_child.calc(weekly_income_for_band),
                income_bands.couple.calc(weekly_income_for_band),
            ],
            default=income_bands.single.calc(weekly_income_for_band),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(
            relevant_income_based_benefit,
            income_bands.single.calc(0),
            banded_support_rate,
        )
