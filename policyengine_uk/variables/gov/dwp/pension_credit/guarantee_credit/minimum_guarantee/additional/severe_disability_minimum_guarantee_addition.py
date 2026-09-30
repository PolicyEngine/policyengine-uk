from policyengine_uk.model_api import *


class severe_disability_minimum_guarantee_addition(Variable):
    label = "Severe disability-related increase"
    documentation = (
        "The additional amount for a severely disabled claimant (State Pension "
        "Credit Regulations 2002 reg 6(4)-(5) and Sch I paras 1-3). A single "
        "claimant qualifies if they receive a qualifying disability benefit, "
        "no other resident aged 18 or over counts, and no carer benefit is "
        "paid for caring for them (para 1(1)(a)). A couple qualify if both "
        "partners receive a qualifying benefit, no other resident counts, and "
        "a carer benefit is paid for at most one of them (para 1(1)(b)); or, "
        "failing that, if one partner receives a qualifying benefit, the other "
        "is certified blind or severely sight impaired, no other resident "
        "counts, and no carer benefit is paid for the first (para 1(1)(c)). "
        "The amount is two rates for a couple under (b) with no carer benefit "
        "paid for either partner, and one rate otherwise (reg 6(5)). The "
        "pension-age Housing Benefit severe disability premium (HB(SPC) Regs "
        "2006 Sch 3 paras 6 and 12(1)) has nearly the same conditions and the "
        "same amounts, but counts an 18- or 19-year-old young person of "
        "another family as a non-dependant, and needs the claimant, not "
        "either partner, to qualify where the other partner is blind. Not "
        "modelled: the hospital-patient deeming (para 1(2)(b)-(bd)) "
        "and backdating (para 1(2)(a), (c)); sight regained within 28 weeks "
        "(para 1(3)); polygamous marriages; and the unmodelled para 2 and 3 "
        "exceptions and carer attribution described on "
        "is_counted_resident_for_severe_disability_addition and "
        "num_severe_disability_addition_qualifiers_cared_for. Blindness "
        "(is_blind) is not in the survey data, so in microsimulation the "
        "blind-partner route never applies and a blind resident is counted."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        severe_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifies = person(
            "receives_severe_disability_addition_qualifying_benefit", period
        )
        qualifying = benunit.sum(claimant_or_partner & qualifies)
        other_partner_blind = benunit.any(
            claimant_or_partner & ~qualifies & person("is_blind", period)
        )
        cared_for = benunit(
            "num_severe_disability_addition_qualifiers_cared_for", period
        )
        # Para 1(1)(b) with reg 6(5): two rates, less one for each partner a
        # carer benefit is paid for (none if paid for both). Para 1(1)(c): one
        # rate. Para 1(1)(a): one rate.
        couple_rates = where(
            qualifying >= 2,
            max_(2 - cared_for, 0),
            (qualifying == 1) & other_partner_blind & (cared_for == 0),
        )
        single_rates = (qualifying >= 1) & (cared_for == 0)
        rates = where(benunit("is_couple", period), couple_rates, single_rates)
        resides_alone = benunit(
            "meets_severe_disability_addition_residence_condition", period
        )
        return rates * resides_alone * severe_disability.addition * WEEKS_IN_YEAR
