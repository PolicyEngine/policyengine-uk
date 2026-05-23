from policyengine_uk.model_api import *


class dartford_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Dartford Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.dartford.council_tax_reduction
        weekly_income = benunit("dartford_council_tax_reduction_weekly_income", period)
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        bands = ctr.income_band
        support_rate = select(
            [
                children >= 2,
                children == 1,
                is_couple,
            ],
            [
                bands.two_or_more_children.calc(weekly_income_for_band),
                bands.one_child.calc(weekly_income_for_band),
                bands.couple.calc(weekly_income_for_band),
            ],
            default=bands.single.calc(weekly_income_for_band),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(relevant_income_based_benefit, 0.8, support_rate)
