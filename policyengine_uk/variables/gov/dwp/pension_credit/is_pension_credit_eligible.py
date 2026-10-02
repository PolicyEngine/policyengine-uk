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
    )

    def formula(benunit, period, parameters):
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        claimant_count = benunit.sum(claimant_or_partner)
        all_claimants_are_sp_age = (
            benunit.sum(claimant_or_partner & benunit.members("is_SP_age", period))
            == claimant_count
        )
        # Mixed-age transitional protection under SI 2019/37 art. 4 is not modelled.
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return (
            (claimant_count > 0)
            & all_claimants_are_sp_age
            & (is_gc_eligible | is_sc_eligible)
        )
