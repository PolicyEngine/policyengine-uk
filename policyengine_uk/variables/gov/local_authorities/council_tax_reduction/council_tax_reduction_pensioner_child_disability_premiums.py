from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit._child_disability_premiums import (
    child_disability_premium_benefit_conditions,
)
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_child_disability_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner child disability premiums"
    documentation = (
        "Councils add the disabled child premium and the enhanced disability "
        "premium to a pensioner's Council Tax Reduction applicable amount for "
        "each child or young person in the family "
        "(is_child_or_young_person_for_council_tax_reduction) who meets the "
        "premium's condition, at the nation's weekly amounts. A child or young "
        "person meets the disabled child condition with a positive DLA or PIP "
        "amount (either component) or the blindness indicator, and the "
        "enhanced condition with the highest DLA care rate "
        "(has_highest_dla_sc_award) or the enhanced PIP daily living rate "
        "(has_enhanced_pip_dl_award), as for Housing Benefit. An armed forces "
        "independence payment meets each condition where the nation's "
        "ministers name it for that person in that year: in England, for a child or "
        "young person for the enhanced premium and for a young person for the "
        "disabled child premium, from 2023-24; in Wales, for a child or young "
        "person for the enhanced premium, and for the disabled child premium "
        "from 2024-25; in Scotland, for a young person for both. A young "
        "person is a Child Benefit qualifying young person "
        "(is_qualifying_young_person_for_child_benefit). The model has no "
        "fields for child disability payment, adult disability payment or "
        "Scottish Adult Disability Living Allowance, so callers enter them in "
        "the DLA and PIP fields. The model omits the hospital limbs and the "
        "section 145A run-on after a child's death. Where the household head "
        "applies alone (council_tax_reduction_head_applies_alone), the model "
        "assumes the head has no children in their family. Working-age "
        "families and families outside England, Wales and Scotland get nil."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/uksi/2023/16/regulation/7/made",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2",
        "https://www.legislation.gov.uk/wsi/2024/56/regulation/5/made",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1",
    )

    def formula(benunit, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        nations = [
            local_authorities.england.council_tax_reduction.pensioners.applicable_amount,
            local_authorities.wales.council_tax_reduction.pensioners.applicable_amount,
            local_authorities.scotland.council_tax_reduction.pensioners.applicable_amount,
        ]
        person = benunit.members
        country = person.household("country", period)
        in_nation = [
            country == Country.ENGLAND,
            country == Country.WALES,
            country == Country.SCOTLAND,
        ]

        def by_nation(get, default):
            return select(in_nation, [get(p) for p in nations], default=default)

        disabled, enhanced = child_disability_premium_benefit_conditions(person, period)
        # The Secretary of State and the Welsh and Scottish Ministers name the
        # armed forces independence payment for a child, a young person, both or
        # neither, by premium and year.
        afip = person("armed_forces_independence_payment", period) > 0
        young_person = person("is_qualifying_young_person_for_child_benefit", period)

        def afip_route(premium):
            routes = [p.armed_forces_independence_payment[premium] for p in nations]
            return afip & where(
                young_person,
                select(in_nation, [r.young_person for r in routes], default=False),
                select(in_nation, [r.child for r in routes], default=False),
            )

        disabled = disabled | afip_route("disabled_child_premium")
        enhanced = enhanced | afip_route("enhanced_disability_premium")
        weekly = (
            by_nation(lambda p: p.disabled_child_premium, 0) * disabled
            + by_nation(lambda p: p.enhanced_disability_premium, 0) * enhanced
        )
        child = person("is_child_or_young_person_for_council_tax_reduction", period)
        pensioner = benunit("council_tax_reduction_pensioner", period)
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        return (
            pensioner * applicant_family * benunit.sum(child * weekly) * WEEKS_IN_YEAR
        )
