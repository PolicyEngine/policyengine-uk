from policyengine_uk.model_api import *


class is_severely_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Severely disabled for the tax credit severe disability elements"
    documentation = (
        "Meets the severe disability condition of the Child Tax Credit "
        "disability element (for a child or qualifying young person) and the "
        "Working Tax Credit severe disability element (for a claimant): the "
        "care component of disability living allowance at the highest rate, "
        "the daily living component of personal independence payment at the "
        "enhanced rate, attendance allowance at the higher rate (a Working "
        "Tax Credit condition; children cannot receive it) or armed forces "
        "independence payment. Other Armed Forces Compensation Scheme "
        "payments do not count. The Scottish equivalents and benefit that "
        "would be payable but for a hospital stay are not modelled. The "
        "legacy severe disability premium has its own, wider list "
        "(receives_severe_disability_premium_qualifying_benefit)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/8",
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/17",
    )

    def formula(person, period, parameters):
        dwp = parameters(period).gov.dwp
        THRESHOLD_SAFETY_GAP = 10 * WEEKS_IN_YEAR
        dla_care_highest = (
            person("dla_sc", period)
            >= dwp.dla.self_care.higher * WEEKS_IN_YEAR - THRESHOLD_SAFETY_GAP
        )
        pip_daily_living_enhanced = (
            person("pip_dl", period)
            >= dwp.pip.daily_living.enhanced * WEEKS_IN_YEAR - THRESHOLD_SAFETY_GAP
        )
        attendance_allowance_higher = (
            person("attendance_allowance", period)
            >= dwp.attendance_allowance.higher * WEEKS_IN_YEAR - THRESHOLD_SAFETY_GAP
        )
        armed_forces_independence_payment = (
            person("armed_forces_independence_payment", period) > 0
        )
        return (
            dla_care_highest
            | pip_daily_living_enhanced
            | attendance_allowance_higher
            | armed_forces_independence_payment
        )
