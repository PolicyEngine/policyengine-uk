from policyengine_uk.model_api import *


class severe_disability_minimum_guarantee_addition(Variable):
    label = "Severe disability-related increase"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        # Count qualifying claimants/partners; children and qualifying young
        # people are ignored under Sch I para 2(2)(f).
        # Sch I para 1(1): a single claimant qualifies if no carer benefit is
        # paid for them (a). A couple qualifies if both partners receive a
        # qualifying benefit and a carer benefit is paid for at most one of
        # them (b), or if one does, the other is blind and no carer benefit is
        # paid for the first (c). Reg 6(5): the double amount applies under (b)
        # when no carer benefit is paid for either partner, otherwise the
        # single amount.
        # Retained simplifications: the household-level non-dependant
        # residence test is not modelled; the person receiving care is not
        # identified, so each carer benefit paid in the benefit unit is assumed
        # to be for a different claimant or partner (for the qualifying
        # partner under (c)); underlying entitlement alone does not count.
        severe_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifies = add(person, period, severe_disability.relevant_benefits) > 0
        qualifying = benunit.sum(claimant_or_partner & qualifies)
        other_partner_blind = benunit.any(
            claimant_or_partner & ~qualifies & person("is_blind", period)
        )
        carers = add(benunit, period, ["receives_carer_benefit"])
        no_carer = carers == 0
        amounts = where(
            benunit("is_couple", period),
            where(
                qualifying >= 2,
                max_(2 - carers, 0),
                (qualifying == 1) & other_partner_blind & no_carer,
            ),
            (qualifying >= 1) & no_carer,
        )
        return amounts * severe_disability.addition * WEEKS_IN_YEAR
