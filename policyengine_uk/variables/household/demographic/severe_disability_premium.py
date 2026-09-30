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
        "paid for both. The law also counts a Universal Credit award with the "
        "carer element, which the model does not."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/20",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/6",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        # The person cared for is not observed. A carer benefit paid to
        # someone in the benefit unit is assumed to be for a claimant or
        # partner other than its recipient, one person per award. Carers in
        # other benefit units are not counted, and carers in other households
        # are not observed. The hospital rules that keep a patient treated as
        # in receipt (and then pay the single rate) are not modelled.
        p = parameters(period).gov.dwp.disability_premia
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifies = person(
            "receives_severe_disability_premium_qualifying_benefit", period
        )
        qualifying_member = claimant_or_partner & qualifies
        qualifying = benunit.sum(qualifying_member)
        partner_treated_as_absent = benunit.any(
            claimant_or_partner & ~qualifies & person("is_blind", period)
        )
        carer = person("receives_carer_benefit", period)
        carers = benunit.sum(carer)
        carers_for_qualifying_member = benunit.sum(carer & ~qualifying_member)
        # Number of single rates payable: two for a couple who both qualify
        # with no carer paid for either, one when a carer is paid for only
        # one of them, and one for a single claimant (or a couple whose
        # other partner is blind) with no carer paid for them.
        couple = benunit("is_couple", period)
        single_condition = where(
            couple,
            (qualifying == 1) & partner_treated_as_absent,
            qualifying >= 1,
        ) & (carers_for_qualifying_member == 0)
        rates = where(
            couple & (qualifying >= 2),
            max_(2 - carers, 0),
            single_condition,
        )
        weekly_amount = select(
            [rates >= 2, rates == 1],
            [p.severe_couple, p.severe_single],
            default=0,
        )
        no_non_dependant = ~benunit(
            "has_non_dependant_for_severe_disability_premium", period
        )
        return weekly_amount * WEEKS_IN_YEAR * no_non_dependant
