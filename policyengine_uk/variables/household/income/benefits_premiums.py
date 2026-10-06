from policyengine_uk.model_api import *

WORKING_AGE_PREMIUMS = [
    "disability_premium",
    "enhanced_disability_premium",
    "severe_disability_premium",
    "carer_premium",
]

# The pension-age schedules (HB(SPC) Regs 2006 Sch 3 Part 3; CTR (Prescribed
# Requirements) (England) Regs 2012 Sch 2 Part 3; the Scottish and Welsh
# pension-age CTR schedules) have only the severe disability, enhanced
# disability (children only), disabled child and carer premiums. The two
# child premiums are not modelled.
PENSION_AGE_PREMIUMS = [
    "pension_age_severe_disability_premium",
    "carer_premium",
]


class working_age_benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Premiums in the working-age schedules"
    documentation = (
        "The disability, enhanced disability, severe disability and carer "
        "premiums, as in the working-age Housing Benefit and Council Tax "
        "Reduction schedules and the Income Support schedule."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2",
    )
    adds = WORKING_AGE_PREMIUMS


class pension_age_benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Premiums in the pension-age schedules"
    documentation = (
        "The severe disability and carer premiums, as in the pension-age "
        "Housing Benefit and Council Tax Reduction schedules, which have no "
        "adult disability or enhanced disability premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1",
        "https://www.legislation.gov.uk/wsi/2013/3035/schedule/2",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
    )
    adds = PENSION_AGE_PREMIUMS


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Value of premiums for disability and carer status"
    documentation = (
        "Premiums in the Housing Benefit applicable amount. Where the claim "
        "falls under the pension-age regulations "
        "(housing_benefit_pension_age_regulations_apply), the pension-age "
        "schedule: the severe disability premium and the carer premium. "
        "Otherwise the working-age schedule. This is the switch the personal "
        "allowance uses. Council Tax Reduction chooses between the same two "
        "schedules with council_tax_reduction_pensioner, and Income Support "
        "uses the working-age schedule."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )

    def formula(benunit, period, parameters):
        return where(
            benunit("housing_benefit_pension_age_regulations_apply", period),
            benunit("pension_age_benefits_premiums", period),
            benunit("working_age_benefits_premiums", period),
        )
