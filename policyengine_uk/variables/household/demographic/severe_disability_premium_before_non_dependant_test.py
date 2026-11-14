from policyengine_uk.model_api import *


class severe_disability_premium_before_non_dependant_test(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium before the non-dependant test"
    documentation = (
        "The shared legacy premium's annual amount after its qualifying-benefit, "
        "partner and carer conditions, before its non-dependant condition. "
        "This is a component, not a paid award. It retains the assumptions and "
        "limitations documented by severe_disability_premium. Council Tax "
        "Reduction can apply its own family definition to this amount."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
    )

    def formula(benunit, period, parameters):
        # Whom a carer benefit is paid for caring for is attributed by
        # is_cared_for_by_carer_benefit_recipient, which the Pension Credit
        # severe disability addition shares. The hospital rules that keep a
        # patient treated as in receipt (and then pay the single rate) are not
        # modelled.
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
        cared_for = benunit.sum(
            qualifying_member
            & person("is_cared_for_by_carer_benefit_recipient", period)
        )
        # Number of single rates payable: two for a couple who both qualify
        # with no carer paid for either, one when a carer is paid for only
        # one of them, and one for a single claimant (or a couple whose
        # other partner is blind) with no carer paid for them.
        couple = benunit("is_couple", period)
        single_condition = where(
            couple,
            (qualifying == 1) & partner_treated_as_absent,
            qualifying >= 1,
        ) & (cared_for == 0)
        rates = where(
            couple & (qualifying >= 2),
            max_(2 - cared_for, 0),
            single_condition,
        )
        weekly_amount = select(
            [rates >= 2, rates == 1],
            [p.severe_couple, p.severe_single],
            default=0,
        )
        return weekly_amount * WEEKS_IN_YEAR
