from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_st_albans_working_age,
)


class st_albans_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "St Albans Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.st_albans.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_st_albans_working_age(local_authority, country, has_pensioner)
        non_dep_deductions_variable = (
            "st_albans_council_tax_reduction_non_dep_deductions"
        )
        legacy_award = legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            non_dep_deductions_variable,
        )
        would_claim_uc = benunit("would_claim_uc", period)
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim_ctr = benunit("would_claim_council_tax_reduction", period)
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(non_dep_deductions_variable, period)
        gross_earnings = add(
            benunit, period, ["employment_income", "self_employment_income"]
        )
        earnings_deductions = add(
            benunit,
            period,
            ["income_tax", "national_insurance", "pension_contributions"],
        )
        monthly_earnings = (
            max_(0, gross_earnings - earnings_deductions) / MONTHS_IN_YEAR
        )
        monthly_contribution = ctr.uc_earnings.contribution.calc(monthly_earnings)
        no_uc_band_entitlement = (
            monthly_earnings >= ctr.uc_earnings.no_entitlement_threshold
        )
        uc_award = max_(
            0,
            liability - monthly_contribution * MONTHS_IN_YEAR - non_dep_deductions,
        )
        uc_award = (
            working_age
            * is_household_head_benunit
            * would_claim_ctr
            * capital_eligible
            * ~no_uc_band_entitlement
            * uc_award
        )
        return where(would_claim_uc, uc_award, legacy_award)
