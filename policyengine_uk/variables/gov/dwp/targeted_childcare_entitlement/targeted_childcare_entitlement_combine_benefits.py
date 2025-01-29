from policyengine_uk.model_api import *


class targeted_childcare_entitlement_combine_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Targeted childcare entitlement based on benefits"
    definition_period = YEAR
    # details for implementation: https://www.gov.uk/help-with-childcare-costs/free-childcare-2-year-olds-claim-benefits?step-by-step-nav=f237ec8e-e82c-4ffa-8fba-2a88a739783b

    def formula(benunit, period, parameters):
        # Calculate total income for the benefit unit
        benunit_income = benunit.sum(benunit.members("total_income", period))
        # Calculate benefits income to exclude from Universal Credit calculation
        benefits_income = benunit.sum(
            benunit.members("social_security_income", period)
        )
        # Income excluding benefits for Universal Credit threshold check
        adjusted_income = benunit_income - benefits_income

        p = parameters(period).gov.dwp.targeted_childcare_entitlement

        # Check if receiving any qualifying benefits
        qualifying_benefits = add(
            benunit,
            period,
            p.qualifying_benefits,
        )

        # Get universal credit receipt specifically for income test
        receives_universal_credit = benunit("universal_credit", period) > 0

        # Get tax credits receipt specifically for income test
        receives_child_tax_credit = benunit("child_tax_credit", period) > 0
        receives_working_tax_credit = benunit("working_tax_credit", period) > 0

        # Check Universal Credit with income threshold
        meets_universal_credit_income = receives_universal_credit & (
            adjusted_income <= p.income_threshold_with_universal_credit
        )

        # Check Tax Credits with income threshold
        meets_tax_credits_income = (
            receives_child_tax_credit | receives_working_tax_credit
        ) & (benunit_income <= p.income_threshold_with_tax_credits)

        return (
            (qualifying_benefits > 0)  # Any qualifying benefit
            | meets_universal_credit_income  # Universal Credit with income threshold
            | meets_tax_credits_income  # Tax Credits with income threshold
        )
