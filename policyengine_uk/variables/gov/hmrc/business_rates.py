from policyengine_uk.model_api import *


class baseline_business_rates(Variable):
    label = "Baseline business rates incidence"
    documentation = (
        "Total incidence from business rates exposure in the baseline"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        br = parameters(period).gov.hmrc.business_rates.statistics.revenue
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
    unit = GBP

    formula = baseline_business_rates.formula


class change_in_business_rates(Variable):
    label = "average per-year business rates"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(business_rates)


class business_rates_change_incidence(Variable):
    label = "Business rates changes"
    documentation = "Total effect of policy changes to business rates"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["business_rates"]
    subtracts = ["baseline_business_rates"]
