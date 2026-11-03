from policyengine_uk.model_api import *


class housing_benefit_main_phase_esa_allowance_adjustment(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit main-phase ESA personal allowance adjustment"
    definition_period = YEAR
    unit = GBP
    documentation = (
        "Replaces the lower age-based working-age adult allowance with its "
        "main-phase ESA amount, using the existing higher allowance parameters. "
        "This is a difference, not an additional personal allowance. Pension-age "
        "allowances and adult premiums are not modified."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/I",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        age = benunit("eldest_claimant_or_partner_age", period)
        single = benunit("is_single_person", period)
        lone_parent = benunit("is_lone_parent", period)
        couple = benunit("is_couple", period)
        qualifies = benunit("housing_benefit_has_main_phase_esa", period) & ~benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        weekly_adjustment = (
            single * (age < p.age_threshold.older) * (p.single.older - p.single.younger)
            + lone_parent
            * (age < p.age_threshold.younger)
            * (p.lone_parent.older - p.lone_parent.younger)
            + couple
            * (age < p.age_threshold.younger)
            * (p.couple.older - p.couple.younger)
        )
        # A reform can reduce a higher allowance below the younger amount.
        # Preserve the signed difference rather than silently overriding it.
        return where(qualifies, weekly_adjustment * WEEKS_IN_YEAR, 0)
