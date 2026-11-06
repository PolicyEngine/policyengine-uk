from policyengine_uk.model_api import *


class enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Enhanced disability premium"
    documentation = (
        "The model pays the legacy benefit enhanced disability premium for "
        "the claimant or partner at the single rate, or at the couple rate "
        "where either or both members of a couple meet the condition "
        "(num_enhanced_disabled_claimants_or_partners_for_legacy_benefits). "
        "The model's Housing Benefit, Income Support and Council Tax "
        "Reduction applicable amounts read it, and Council Tax Reduction "
        "replaces it with its own scheme's premium "
        "(council_tax_reduction_enhanced_disability_premium). "
        "housing_benefit_child_disability_premiums computes Housing Benefit's "
        "separate enhanced rate for children and young persons."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/4",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.enhanced_single
        couple_premium = couple * dis.enhanced_couple
        has_enhanced_disabled_claimant_or_partner = (
            benunit(
                "num_enhanced_disabled_claimants_or_partners_for_legacy_benefits",
                period,
            )
            > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_enhanced_disabled_claimant_or_partner
