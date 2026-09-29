from policyengine_uk.model_api import *


class is_pension_credit_eligible(Variable):
    label = "Eligible for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        is_sp_age = benunit.members("is_SP_age", period)
        claimant_count = benunit.sum(claimant_or_partner)
        sp_age_count = benunit.sum(claimant_or_partner & is_sp_age)
        # SPCA 2002 s.1(2)(b): the claimant must have attained the qualifying
        # age.
        has_qualifying_age_claimant = sp_age_count > 0
        # SPCA 2002 s.4(1A), from 15 May 2019: a partner below the qualifying
        # age bars entitlement, unless SI 2019/37 art. 4 saves the couple.
        mixed_age_couple = sp_age_count < claimant_count
        excluded_as_mixed_age_couple = (
            p.mixed_age_couple_exclusion.in_effect
            & mixed_age_couple
            & ~benunit("is_protected_mixed_age_couple_for_pension_credit", period)
        )
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return (
            has_qualifying_age_claimant
            & ~excluded_as_mixed_age_couple
            & (is_gc_eligible | is_sc_eligible)
        )
