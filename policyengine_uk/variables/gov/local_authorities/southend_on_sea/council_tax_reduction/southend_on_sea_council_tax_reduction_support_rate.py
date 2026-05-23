from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Southend-on-Sea Council Tax Reduction support rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.southend_on_sea.council_tax_reduction
        weekly_income = benunit(
            "southend_on_sea_council_tax_reduction_weekly_income", period
        )
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        bands = ctr.income_band
        base_rate = select(
            [num_children >= 2, num_children == 1],
            [
                bands.two_or_more_children.calc(weekly_income_for_band),
                bands.one_child.calc(weekly_income_for_band),
            ],
            default=bands.no_children.calc(weekly_income_for_band),
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(relevant_income_based_benefit, 0.75, base_rate)
