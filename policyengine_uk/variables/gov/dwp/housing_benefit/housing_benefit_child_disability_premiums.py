from policyengine_uk.model_api import *


class housing_benefit_child_disability_premiums(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit disabled-child and enhanced-child premiums"
    documentation = "Both premiums are additional to child personal allowances and adult premiums. They are not subject to the historical two-child personal-allowance limit. Actual listed benefit awards, hospital suspension, blindness and statutory post-death Child Benefit continuation establish the separate conditions; a general disability indicator does not."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/7",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/8",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        person = benunit.members
        child = person("is_child_or_young_person_for_legacy_benefits", period)
        listed = (
            add(person, period, ["dla", "pip", "armed_forces_independence_payment"]) > 0
        )
        suspended_or_scottish = person(
            "housing_benefit_child_disability_payment_or_suspension", period
        )
        ceased = person("housing_benefit_childcare_blind_certification_ceased", period)
        now = person.benunit("housing_benefit_assessment_date", period)
        weeks = parameters(period).gov.dwp.housing_benefit.blindness_run_on_weeks
        blind = person("is_blind", period) | (
            (now >= ceased) & (now < ceased + np.timedelta64(int(weeks * 7), "D"))
        )
        disabled = child & (listed | suspended_or_scottish | blind)
        dla = person("dla_sc_category", period)
        pip = person("pip_dl_category", period)
        enhanced = child & (
            ((dla == dla.possible_values.HIGHER) & (person("dla", period) > 0))
            | ((pip == pip.possible_values.ENHANCED) & (person("pip", period) > 0))
            | (person("armed_forces_independence_payment", period) > 0)
            | person(
                "housing_benefit_child_enhanced_disability_payment_or_suspension",
                period,
            )
        )
        after_death = person("housing_benefit_child_benefit_after_death", period)
        disabled |= enhanced
        disabled |= after_death & person(
            "housing_benefit_disabled_child_premium_before_death", period
        )
        enhanced |= after_death & person(
            "housing_benefit_enhanced_child_premium_before_death", period
        )
        return WEEKS_IN_YEAR * (
            benunit.sum(disabled) * p.disabled_child_premium
            + benunit.sum(enhanced) * p.enhanced_child_premium
        )
