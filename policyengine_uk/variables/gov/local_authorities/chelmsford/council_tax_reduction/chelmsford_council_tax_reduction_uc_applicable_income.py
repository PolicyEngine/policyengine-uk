from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chelmsford Local Council Tax Support Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.dwp.universal_credit.means_test
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        weekly_disregard = benunit(
            "chelmsford_council_tax_reduction_earnings_disregard", period
        )
        earned_income = max_(
            0,
            benunit("uc_earned_income", period) - weekly_disregard * WEEKS_IN_YEAR,
        )
        source_disregarded_income = benunit(
            "chelmsford_council_tax_reduction_source_disregarded_income", period
        )
        unearned_income = max_(
            0,
            benunit("uc_unearned_income", period) - source_disregarded_income,
        )
        remaining_uc_award = max_(
            0,
            uc_award_before_deductions
            - benunit("uc_housing_costs_element", period)
            - benunit("uc_disability_elements", period),
        )
        uc_maximum_amount = benunit("uc_maximum_amount", period)
        uc_income_reduction = min_(
            uc_maximum_amount,
            ctr.reduction_rate * benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period),
        )
        safe_uc_maximum_amount = max_(uc_maximum_amount, 1)
        proportion = (
            (uc_maximum_amount > 0) * remaining_uc_award / safe_uc_maximum_amount
        )
        adjusted_uc_award = max_(
            0,
            remaining_uc_award - proportion * uc_income_reduction,
        )
        return has_uc_award * (earned_income + unearned_income + adjusted_uc_award)
