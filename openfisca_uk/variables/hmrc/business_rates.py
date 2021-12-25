from openfisca_uk.model_api import *


class baseline_business_rates(Variable):
    label = "Baseline business rates incidence"
    documentation = (
        "Total incidence from business rates exposure in the baseline"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        br = parameters(period).hmrc.business_rates.statistics.revenue
        total_revenue = (
            br.ENGLAND  # HMRC
            + br.SCOTLAND  # Revenue Scotland
            + br.WALES  # Welsh Revenue Authority
            + br.NORTHERN_IRELAND  # HMRC
        )
        return household("shareholding", period) * total_revenue


class business_rates(Variable):
    label = "Business rates incidence"
    documentation = "Total incidence from exposure to business rates via corporate shareholdings"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    formula = baseline_business_rates.formula


class business_rates_change_incidence(Variable):
    label = "Business rates changes"
    documentation = "Total effet of policy changes to business rates"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        business_rates = household("business_rates", period)
        baseline_business_rates = household("baseline_business_rates", period)
        return business_rates - baseline_business_rates
