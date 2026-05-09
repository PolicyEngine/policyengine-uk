from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire Council Tax Reduction weekly earned income"
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://beta.southglos.gov.uk/apply-for-council-tax-reduction/",
        "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf",
    ]

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_gloucestershire.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        deductions = (
            person("income_tax", period)
            + person("national_insurance", period)
            + person("pension_contributions", period)
        )
        employment_income = person("employment_income", period)
        self_employment_income = person("self_employment_income", period)
        actual_net_earnings = max_(
            0, employment_income + self_employment_income - deductions
        )
        net_employment_income = max_(0, employment_income - deductions)
        self_employment_floor = (
            ctr.self_employment_floor.weekly_hours
            * ctr.self_employment_floor.hourly_rate
            * WEEKS_IN_YEAR
        )
        floor_applies = person(
            "south_gloucestershire_council_tax_reduction_self_employment_floor_applies",
            period,
        )
        floor_net_earnings = net_employment_income + max_(
            0, self_employment_floor - net_employment_income
        )
        non_uc_person_earnings = where(
            floor_applies,
            max_(actual_net_earnings, floor_net_earnings),
            actual_net_earnings,
        )
        non_uc_earnings = benunit.sum(claimant_or_partner * non_uc_person_earnings)

        uc_gross_earnings = person("uc_mif_capped_earned_income", period)
        uc_mif_applies = person("uc_mif_applies", period)
        uc_net_earnings = where(
            uc_mif_applies,
            uc_gross_earnings,
            max_(0, uc_gross_earnings - deductions),
        )
        uc_earnings = benunit.sum(claimant_or_partner * uc_net_earnings)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        annual_earnings = where(has_uc_award, uc_earnings, non_uc_earnings)
        return annual_earnings / WEEKS_IN_YEAR
