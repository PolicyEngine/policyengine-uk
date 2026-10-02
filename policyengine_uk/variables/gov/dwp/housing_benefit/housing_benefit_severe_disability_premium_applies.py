from policyengine_uk.model_api import *


class housing_benefit_severe_disability_premium_applies(Variable):
    value_type = bool
    entity = BenUnit
    label = "Severe disability premium conditions met (Housing Benefit)"
    documentation = (
        "Whether the claimant is a severely disabled person for the Housing "
        "Benefit severe disability premium (HB Regs 2006 Sch 3 para 14): the "
        "claimant (and any partner) receives a qualifying disability benefit, "
        "and no non-dependant aged 18 or over normally resides with them, "
        "other than one who receives a qualifying benefit. Within the family "
        "a non-dependant is an adult who is neither the claimant nor partner "
        "nor a child or young person; outside it, the household composition "
        "proxy of lha_renter_has_non_dependant (another benefit unit's "
        "claimant or partner). Not modelled: who receives carer's allowance, "
        "carer support payment or the UC carer element for caring for the "
        "claimant, and the treatment of a blind partner. The legacy "
        "severe_disability_premium variable uses the tax credit definition of "
        "severe disability, which is narrower."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.severe_disability_premium
        person = benunit.members
        qualifying = add(person, period, p.qualifying_benefits) > 0
        claimant_or_partner = person("is_claimant_or_partner", period)
        # Sch 3 para 14(2)(a)(i), (b)(i)-(ii): every claimant or partner
        # receives a qualifying benefit.
        all_qualify = benunit.all(qualifying | ~claimant_or_partner) & benunit.any(
            claimant_or_partner
        )
        # Para 14(2)(a)(ii), (b)(iii) with (4): no non-dependant aged 18 or
        # over, disregarding one who receives a qualifying benefit.
        age = person("age", period)
        adult_non_dependant = (age >= 18) & ~qualifying
        young_person = person("is_child_or_young_person_for_legacy_benefits", period)
        within = benunit.any(adult_non_dependant & ~claimant_or_partner & ~young_person)
        other_claimants = benunit.max(
            person.household.sum(adult_non_dependant & claimant_or_partner)
        ) - benunit.sum(adult_non_dependant & claimant_or_partner)
        return all_qualify & ~within & ~(other_claimants > 0)
