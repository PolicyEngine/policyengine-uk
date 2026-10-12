from policyengine_uk.model_api import *


class housing_benefit_specified_or_temporary_accommodation_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit specified or temporary accommodation earnings disregard"
    documentation = (
        "The amount, from 5 October 2026, that the working-age Regulations "
        "disregard from the net earnings of a claimant who lives in specified "
        "or temporary accommodation where the claimant or partner is an "
        "employed or self-employed earner: £61.41 a week for a single "
        "claimant or lone parent under 25 and £77.73 at 25 or over; for a "
        "couple, £97.33 where both are under 18, £61.53 where one is 18 or "
        "over but both are under 25, and £119.70 where one is 25 or over. A "
        "couple has one amount, taken from the claimant's earnings and then "
        "from the partner's. This is the full amount; "
        "housing_benefit_applicable_income_disregard adds it to the other "
        "disregards and caps the total at net earnings. The pension-age "
        "Regulations have no such disregard. The model reads each fiscal year "
        "at 30 April, so it is zero for 2026-27 and in full from 2027-28."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2026/753/regulation/2",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation
        person = benunit.members
        # Para 18(1)(b): the claimant or partner is an employed earner or a
        # self-employed earner. Anyone with earnings is, including statutory
        # sick or maternity pay from a continuing employment and a
        # self-employment loss. The amount is capped at net earnings in
        # housing_benefit_applicable_income_disregard, so a family without
        # net earnings gets nothing either way.
        earner = (
            (person("employment_income", period) > 0)
            | (person("self_employment_income", period) != 0)
            | (person("employment_benefits", period) > 0)
        )
        has_earner = benunit.any(person("is_claimant_or_partner", period) & earner)
        # Para 18(2): the claimant's age, or the elder member's for a couple.
        eldest = benunit("eldest_claimant_or_partner_age", period)
        older = eldest >= p.age_threshold.older
        couple_amount = select(
            [older, eldest >= p.age_threshold.younger],
            [p.couple.older, p.couple.younger],
            default=p.couple.minors,
        )
        weekly_amount = select(
            [benunit("is_lone_parent", period), benunit("is_couple", period)],
            [
                where(older, p.lone_parent.older, p.lone_parent.younger),
                couple_amount,
            ],
            default=where(older, p.single.older, p.single.younger),
        )
        # Para 18(1)(a), and only in the working-age Regulations (SI 2006/213;
        # NI SR 2006/405): SI 2006/214 and SR 2006/406 are not amended.
        applies = (
            benunit("in_specified_or_temporary_accommodation", period)
            & has_earner
            & ~benunit("housing_benefit_pension_age_regulations_apply", period)
        )
        return where(applies, weekly_amount * WEEKS_IN_YEAR, 0)
