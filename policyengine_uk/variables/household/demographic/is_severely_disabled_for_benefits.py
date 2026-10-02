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
        "would be payable but for a hospital stay are not modelled. "
        "Attendance allowance is read from its award category (aa_category), "
        "which the Enhanced FRS holds. Only where no category is given, as "
        "when a household enters an attendance allowance amount directly, is "
        "the amount compared with the annual higher rate, less £10 a week; "
        "the Regulations have no such tolerance, so that fallback is an "
        "approximation. The disability living allowance and personal "
        "independence payment tests read amounts, which the model computes "
        "from their categories, with the same tolerance for amounts entered "
        "directly. The Enhanced FRS also stores this flag, and dataset runs "
        "use the stored value instead of this formula "
        "(policyengine-uk-data#494 aligns its definition with this one). "
        "The legacy severe disability premium has its own, wider list "
        "(receives_severe_disability_premium_qualifying_benefit). The flag "
        "also gates the Universal Credit higher disabled child addition, "
        "whose condition (UC Regs 2013 reg 24(2)(b)) adds blindness and has "
        "no armed forces independence payment limb; that is not yet separated."
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
        # WTC Regs 2002 reg 17(2): "an attendance allowance at the higher
        # rate". The award category decides; an amount is read only when no
        # category is given.
        aa_category = person("aa_category", period)
        aa_categories = aa_category.possible_values
        attendance_allowance_higher = where(
            aa_category == aa_categories.NONE,
            person("attendance_allowance", period)
            >= dwp.attendance_allowance.higher * WEEKS_IN_YEAR - THRESHOLD_SAFETY_GAP,
            aa_category == aa_categories.HIGHER,
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
