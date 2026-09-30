from policyengine_uk.model_api import *


class has_non_dependant_for_severe_disability_premium(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant who blocks the severe disability premium"
    documentation = (
        "A non-dependant aged 18 or over normally resides with the claimant, "
        "which bars the legacy severe disability premium. Non-dependants who "
        "receive a severe disability premium qualifying benefit, or who are "
        "blind, are ignored. Every household member aged 18 or over outside "
        "the benefit unit is treated as a non-dependant. The model cannot "
        "identify the people the Regulations exclude from that definition "
        "(joint occupiers, and commercial lodgers or landlords who are not "
        "close relatives), or someone who is treated as blind for 28 weeks "
        "after regaining their sight."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/3",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        person = benunit.members
        counted = (
            (person("age", period) >= p.severe_non_dependant_age)
            & ~person("receives_severe_disability_premium_qualifying_benefit", period)
            & ~person("is_blind", period)
        )
        # Counted residents of the household, less those in this benefit unit.
        in_household = benunit.max(person.household.sum(counted))
        return in_household > benunit.sum(counted)
