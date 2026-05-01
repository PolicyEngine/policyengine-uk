from policyengine_uk.model_api import *


class croydon_council_tax_reduction_disabled_not_working(Variable):
    value_type = bool
    entity = BenUnit
    label = "Croydon Council Tax Support disabled non-working group"
    definition_period = YEAR
    reference = "https://www.croydon.gov.uk/benefits/changes-council-tax-support/how-we-work-out-amount-council-tax-support"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        has_uc = person.benunit("universal_credit", period) > 0
        benunit_has_uc = benunit("universal_credit", period) > 0
        has_earned_income = where(
            benunit_has_uc,
            benunit("uc_earned_income", period) > 0,
            benunit.sum(claimant_or_partner * earned_income) > 0,
        )
        disabled_or_lcw = (
            (person("pip", period) > 0)
            | (person("dla", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("incapacity_benefit", period) > 0)
            | person("is_disabled_for_benefits", period)
            | person("is_blind", period)
            | (has_uc & person("uc_limited_capability_for_WRA", period))
        )
        disabled_claimant_or_partner = benunit.any(
            claimant_or_partner & disabled_or_lcw
        )
        income_related_esa = benunit("esa_income", period) > 0
        tax_credit_disability = (
            (benunit("WTC_disabled_element", period) > 0)
            | (benunit("WTC_severely_disabled_element", period) > 0)
            | (benunit("uc_LCWRA_element", period) > 0)
        )
        return (
            disabled_claimant_or_partner | income_related_esa | tax_credit_disability
        ) & ~has_earned_income
