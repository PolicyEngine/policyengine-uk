from policyengine_uk.model_api import *


class pension_age_severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium for pension-age Housing Benefit and CTR"
    documentation = (
        "The severe disability premium in the Housing Benefit and Council Tax "
        "Reduction applicable amount of a family whose claimant or partner has "
        "reached the qualifying age for State Pension Credit. "
        "HB(SPC) Regs 2006 Sch 3 para 6 sets the same conditions as the "
        "working-age premium (HB Regs 2006 Sch 3 para 14): the qualifying "
        "benefits, both partners qualifying unless the other is blind, no "
        "non-dependant aged 18 or over with the same exceptions (para 6(6), "
        "reg 3), and no carer benefit paid for caring for the claimant or "
        "partner. Para 12 sets the same weekly amounts. So this is "
        "severe_disability_premium for such a family, with "
        "its amounts and its documented assumptions: where only one partner "
        "qualifies and the other is blind, the qualifying partner is taken to "
        "claim, as a couple may agree under HB(SPC) reg 63(1) and the CTR "
        "schemes (England SI 2012/2885 Sch 8 para 4(1)); carers are attributed "
        "by is_cared_for_by_carer_benefit_recipient, which does not count "
        "Universal Credit carer-element awards. The Pension Credit severe "
        "disability addition has the same conditions apart from its wider "
        "residence exceptions, but its own amount parameter, so a Pension "
        "Credit reform does not move this premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/63",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/8/paragraph/4",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        # HB(SPC) Regs 2006 reg 5 and the CTR pensioner tests turn on a
        # claimant or partner having attained the qualifying age for State
        # Pension Credit; each programme's own switch then chooses the
        # schedule (benefits_premiums, council_tax_reduction_applicable_amount).
        person = benunit.members
        over_qualifying_age = benunit.any(
            person("is_claimant_or_partner", period)
            & person("has_attained_state_pension_credit_qualifying_age", period)
        )
        return where(
            over_qualifying_age, benunit("severe_disability_premium", period), 0
        )
