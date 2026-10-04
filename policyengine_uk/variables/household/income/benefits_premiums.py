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


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Value of premiums for disability and carer status"
    documentation = (
        "Premiums in the Housing Benefit, Council Tax Reduction and Income "
        "Support applicable amounts. A family with a member over State "
        "Pension age uses the pension-age schedules: the severe disability "
        "premium and the carer premium. Those schedules have no adult disability or "
        "enhanced disability premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1",
        "https://www.legislation.gov.uk/wsi/2013/3035/schedule/2",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2",
    )

    def formula(benunit, period, parameters):
        # Same switch as the aged personal allowance in the Housing Benefit
        # and Council Tax Reduction applicable amounts. Income Support is not
        # paid to a family with a member over State Pension age.
        pension_age = benunit.any(benunit.members("is_SP_age", period))
        return where(
            pension_age,
            add(benunit, period, PENSION_AGE_PREMIUMS),
            add(benunit, period, WORKING_AGE_PREMIUMS),
        )
