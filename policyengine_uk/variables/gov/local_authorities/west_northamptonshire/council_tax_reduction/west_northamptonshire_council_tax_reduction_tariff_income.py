from policyengine_uk.model_api import *
import numpy as np


class west_northamptonshire_council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "West Northamptonshire Council Tax Reduction tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"

    def formula(benunit, period, parameters):
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        tariff = parameters(
            period
        ).gov.local_authorities.west_northamptonshire.council_tax_reduction.means_test.tariff_income
        capital = benunit.household("savings", period)
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.ceil(excess_capital / tariff.step)
        tariff_income = tariff_units * tariff.amount * WEEKS_IN_YEAR
        return where(has_uc_award | relevant_income_based_benefit, 0, tariff_income)
