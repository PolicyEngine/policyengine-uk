from policyengine_uk.model_api import *


class housing_benefit_severe_disability_premium_applies(Variable):
    value_type = bool
    entity = BenUnit
    label = "Severe disability premium conditions met (Housing Benefit)"
    documentation = (
        "Whether the claimant is a severely disabled person for the Housing "
        "Benefit severe disability premium: the claimant (and any partner) "
        "receives a qualifying disability benefit, and no non-dependant aged "
        "18 or over normally resides with them, other than one who receives "
        "a qualifying benefit or is blind. A partner who is blind and "
        "receives no qualifying benefit is treated as not being the "
        "claimant's partner, so the claimant is tested as a single person. "
        "Not modelled: who receives Carer's Allowance, Carer Support Payment "
        "or the UC carer element for caring for the claimant. The legacy "
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
        blind = person("is_blind", period)
        # Sch 3 para 14(2)(a)(i), (b)(i)-(ii): every claimant or partner
        # receives a qualifying benefit. Para 14(3) (pension age: Sch 3 para
        # 6(3)): a partner who does not, and is blind, is treated as not
        # being the claimant's partner, so the other member is tested as a
        # single claimant under (2)(a) and must receive one.
        all_qualify = benunit.all(
            qualifying | blind | ~claimant_or_partner
        ) & benunit.any(claimant_or_partner & qualifying)
        # Para 14(2)(a)(ii), (b)(iii) with (4): no non-dependant aged 18 or
        # over, disregarding one who receives a qualifying benefit or is
        # blind. Within the family, an adult who is neither claimant nor
        # partner nor a child or young person; outside it, as for
        # housing_benefit_has_non_dependant.
        age = person("age", period)
        adult_non_dependant = (age >= 18) & ~qualifying & ~blind
        young_person = person("is_child_or_young_person_for_legacy_benefits", period)
        within = benunit.any(adult_non_dependant & ~claimant_or_partner & ~young_person)
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        outside = benunit.max(
            person.household.sum(
                adult_non_dependant
                & person("is_non_dependant_of_household_head", period)
            )
        )
        return all_qualify & ~within & ~(liable_family & (outside > 0))
