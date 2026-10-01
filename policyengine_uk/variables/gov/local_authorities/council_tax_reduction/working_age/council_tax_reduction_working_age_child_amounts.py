from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_child_amounts(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction amounts for children"
    documentation = (
        "Annual amounts in a working-age applicable amount in Scotland or "
        "Wales for the children and young persons in the family: the child "
        "premium (Scotland) or child or young person amount (Wales) for each "
        "one, the family premium, and the disabled child premium and "
        "child enhanced disability premium. There is no limit on the number "
        "of children. A child or young person with a disability benefit or "
        "who is blind gets the disabled child premium; one with the highest "
        "rate of the care component of disability living allowance or the "
        "enhanced daily living component of personal independence payment "
        "also gets the enhanced disability premium, the same test the model "
        "uses for Universal Credit's higher disabled child addition. "
        "Scotland removed the family premium for new claims from 1 May "
        "2016; it survives only as a transitional premium for families with "
        "an unbroken claim since then, which the model does not track."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/35",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/4",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        scot = p.scotland.council_tax_reduction.working_age
        wales = p.wales.council_tax_reduction.working_age
        scotland = is_scotland_scheme(benunit.household("country", period))
        person = benunit.members
        child = person("is_child_or_young_person_for_legacy_benefits", period)
        disabled = person("is_disabled_for_benefits", period) | person(
            "is_blind", period
        )
        severely_disabled = person("is_severely_disabled_for_benefits", period)
        children = benunit.sum(child)
        disabled_children = benunit.sum(child & (disabled | severely_disabled))
        severely_disabled_children = benunit.sum(child & severely_disabled)
        per_child = where(scotland, scot.child_premium, wales.child_amount)
        family_premium = (children > 0) * where(
            scotland, scot.family_premium, wales.family_premium
        )
        disabled_child_premium = where(
            scotland, scot.disabled_child_premium, wales.disabled_child_premium
        )
        child_enhanced_disability_premium = where(
            scotland,
            scot.child_enhanced_disability_premium,
            wales.child_enhanced_disability_premium,
        )
        weekly = (
            children * per_child
            + family_premium
            + disabled_children * disabled_child_premium
            + severely_disabled_children * child_enhanced_disability_premium
        )
        return weekly * WEEKS_IN_YEAR
