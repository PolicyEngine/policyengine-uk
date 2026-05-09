from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_derbyshire.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        non_uc_applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        ) + benunit("south_derbyshire_council_tax_reduction_tariff_income", period)
        uc_applicable_income = benunit(
            "south_derbyshire_council_tax_reduction_uc_applicable_income", period
        )
        applicable_income = where(
            has_uc_award, uc_applicable_income, non_uc_applicable_income
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        # Keep exact penny thresholds from landing below source lower limits after float rounding.
        weekly_excess_income = np.round(excess_income / WEEKS_IN_YEAR, 2) + 0.005
        return ctr.income_band.support_rate.calc(weekly_excess_income)
