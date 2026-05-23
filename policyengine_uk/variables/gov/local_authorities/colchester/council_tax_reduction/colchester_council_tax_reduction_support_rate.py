from policyengine_uk.model_api import *


class colchester_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester Council Tax Reduction support rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.colchester.council_tax_reduction
        weekly_income = benunit(
            "colchester_council_tax_reduction_weekly_income", period
        )
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        bands = ctr.income_band
        banded_support_rate = select(
            [
                is_couple & (num_children >= 2),
                is_couple & (num_children == 1),
                (~is_couple) & (num_children >= 2),
                (~is_couple) & (num_children == 1),
                is_couple,
            ],
            [
                bands.couple_two_or_more_children.calc(weekly_income_for_band),
                bands.couple_one_child.calc(weekly_income_for_band),
                bands.single_two_or_more_children.calc(weekly_income_for_band),
                bands.single_one_child.calc(weekly_income_for_band),
                bands.couple.calc(weekly_income_for_band),
            ],
            default=bands.single.calc(weekly_income_for_band),
        )
        protected = benunit("colchester_council_tax_reduction_protected_group", period)
        protected_support_rate = bands.protected.calc(weekly_income_for_band)
        return where(protected, protected_support_rate, banded_support_rate)
