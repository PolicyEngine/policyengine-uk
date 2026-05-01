from policyengine_uk.model_api import *


class croydon_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Croydon Council Tax Support weekly household income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.croydon.gov.uk/benefits/changes-council-tax-support/how-we-work-out-amount-council-tax-support"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.croydon.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        gross_earnings = benunit.sum(claimant_or_partner * earned_income)
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        net_earnings = max_(0, gross_earnings - earnings_deductions)
        other_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "property_income",
                    "private_pension_income",
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "miscellaneous_income",
                ],
            )
        )
        benefit_income = add(
            benunit,
            period,
            [
                "income_support",
                "jsa_income",
                "jsa_contrib",
                "esa_income",
                "esa_contrib",
                "housing_benefit",
                "pension_credit",
                "working_tax_credit",
                "child_tax_credit",
                "carers_allowance",
            ],
        )
        non_uc_income = max_(0, net_earnings + other_income + benefit_income)
        has_uc = benunit("universal_credit", period) > 0
        uc_income = max_(
            0,
            benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period)
            + benunit(
                "croydon_council_tax_reduction_countable_universal_credit", period
            ),
        )
        annual_income = where(has_uc, uc_income, non_uc_income)

        disabled_not_working = benunit(
            "croydon_council_tax_reduction_disabled_not_working", period
        )
        person_has_uc = person.benunit("universal_credit", period) > 0
        disability_or_lcw = (
            (person("pip", period) > 0)
            | (person("dla", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("incapacity_benefit", period) > 0)
            | person("is_disabled_for_benefits", period)
            | person("is_blind", period)
            | (person_has_uc & person("uc_limited_capability_for_WRA", period))
        )
        disabled_claim = disabled_not_working | benunit.any(
            claimant_or_partner & disability_or_lcw
        )
        has_earnings = where(
            has_uc,
            benunit("uc_earned_income", period) > 0,
            gross_earnings > 0,
        )
        weekly_income = annual_income / WEEKS_IN_YEAR
        weekly_disregard = where(
            disabled_claim & has_earnings,
            ctr.disabled_working_weekly_income_disregard,
            0,
        )
        return max_(0, weekly_income - weekly_disregard)
