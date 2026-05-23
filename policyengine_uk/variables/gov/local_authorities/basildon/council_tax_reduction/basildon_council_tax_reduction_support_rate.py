from policyengine_uk.model_api import *


class basildon_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Basildon Council Tax Reduction support rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.basildon.council_tax_reduction
        weekly_income = benunit("basildon_council_tax_reduction_weekly_income", period)
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        num_dependants = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        bands = ctr.income_band
        base_rate = select(
            [
                num_dependants >= 2,
                num_dependants == 1,
            ],
            [
                bands.two_or_more_dependants.calc(weekly_income_for_band),
                bands.one_dependent.calc(weekly_income_for_band),
            ],
            default=bands.no_dependants.calc(weekly_income_for_band),
        )
        protected = benunit("basildon_council_tax_reduction_protected_group", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(
            relevant_income_based_benefit | (protected & (base_rate > 0)),
            0.75,
            base_rate,
        )
