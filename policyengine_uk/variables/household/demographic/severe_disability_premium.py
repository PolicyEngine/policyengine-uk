from policyengine_uk.model_api import *


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium"
    documentation = (
        "Legacy benefit severe disability premium. A single claimant qualifies "
        "if they receive a qualifying benefit; a couple qualifies only if both "
        "partners do, or if one does and the other is blind (the blind "
        "partner is then treated as absent and the single rate applies). The "
        "Regulations treat only the claimant's blind partner as absent; the "
        "model assumes the qualifying partner is the claimant, as a couple "
        "can arrange for Housing Benefit (HB Regs reg 82(1)). There must be "
        "no non-dependant aged 18 or over, other than one who receives a "
        "qualifying benefit or is blind. A single claimant (or one whose blind "
        "partner is treated as absent) must have no one paid a carer benefit "
        "for caring for them. A couple who both qualify get the double rate "
        "when no carer benefit is paid for either of them, the single rate "
        "when one is paid for only one of them, and nothing when carers are "
        "paid for both. Whom a carer benefit is paid for caring for is "
        "attributed by is_cared_for_by_carer_benefit_recipient, shared with "
        "the Pension Credit severe disability addition; the law also counts "
        "a Universal Credit award with the carer element, which the model "
        "does not. Not modelled: a carer's "
        "allowance or carer element that would be paid but for a loss of "
        "benefit restriction under section 6B or 7 of the Social Security "
        "Fraud Act 2001 also counts (HB Regs 2006 Sch 3 para 14(7), IS Regs "
        "1987 Sch 2 para 13(5), ESA Regs 2008 Sch 4 para 6(8), JSA Regs 1996 "
        "Sch 1 para 15(9)); the model has no input for such a restriction, so "
        "where one applies it can pay a premium the law withholds. The "
        "Jobseeker's Allowance savings for people protected by the Income "
        "Support (General) Amendment (No. 6) Regulations 1991 (JSA Regs 1996 "
        "Sch 1 para 15(8)) are not modelled; income-based Jobseeker's "
        "Allowance is a reported amount in the model, so this changes no "
        "modelled payment."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/4",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/6",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15",
        "https://www.legislation.gov.uk/ukpga/2001/11/section/6B",
        "https://www.legislation.gov.uk/ukpga/2001/11/section/7",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        amount = benunit("severe_disability_premium_before_non_dependant_test", period)
        no_non_dependant = ~benunit(
            "has_non_dependant_for_severe_disability_premium", period
        )
        return amount * no_non_dependant
