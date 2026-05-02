from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support weekly earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.plymouth.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        has_children = benunit.any(child_or_young_person)
        family_with_child = has_children & (
            benunit("is_lone_parent", period) | benunit("is_couple", period)
        )
        disability_or_esa = benunit(
            "plymouth_council_tax_reduction_disability_or_esa_component", period
        )
        special_occupation = benunit(
            "plymouth_council_tax_reduction_source_special_earnings_disregard", period
        )
        return select(
            [
                family_with_child,
                disability_or_esa | special_occupation,
                benunit("is_couple", period),
                benunit("is_single_person", period),
            ],
            [
                ctr.earnings_disregard.lone_parent_or_couple_with_child,
                ctr.earnings_disregard.disability_or_esa_component,
                ctr.earnings_disregard.couple,
                ctr.earnings_disregard.single,
            ],
            default=0,
        )
