from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support weekly earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cotswold.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        carer_or_disability = (
            benunit.any(claimant_or_partner & (person("carers_allowance", period) > 0))
            | (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | (benunit("enhanced_disability_premium", period) > 0)
            | benunit.any(
                claimant_or_partner
                & (
                    (person("pip", period) > 0)
                    | (person("dla", period) > 0)
                    | (person("armed_forces_independence_payment", period) > 0)
                )
            )
        )
        base = select(
            [
                benunit("is_lone_parent", period),
                carer_or_disability,
                benunit("is_couple", period),
                benunit("is_single_person", period),
            ],
            [
                ctr.earnings_disregard.lone_parent,
                ctr.earnings_disregard.carer_or_disability,
                ctr.earnings_disregard.couple,
                ctr.earnings_disregard.single,
            ],
            default=0,
        )
        additional = (
            benunit(
                "cotswold_council_tax_reduction_source_additional_earnings_disregard",
                period,
            )
            * ctr.earnings_disregard.additional
        )
        return base + additional
