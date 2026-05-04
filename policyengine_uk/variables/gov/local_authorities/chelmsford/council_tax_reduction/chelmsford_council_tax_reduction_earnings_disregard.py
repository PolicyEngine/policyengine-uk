from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Chelmsford Local Council Tax Support weekly earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.chelmsford.council_tax_reduction
        disability_or_esa = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | (
                benunit(
                    "chelmsford_council_tax_reduction_esa_support_component", period
                )
                > 0
            )
        )
        carer = benunit("carer_premium", period) > 0
        special_occupation = benunit(
            "chelmsford_council_tax_reduction_source_special_earnings_disregard",
            period,
        )
        return select(
            [
                benunit("is_lone_parent", period),
                carer,
                special_occupation,
                disability_or_esa,
                benunit("is_couple", period),
                benunit("is_single_person", period),
            ],
            [
                ctr.earnings_disregard.lone_parent,
                ctr.earnings_disregard.carer,
                ctr.earnings_disregard.special_occupation,
                ctr.earnings_disregard.disability_or_esa_component,
                ctr.earnings_disregard.couple,
                ctr.earnings_disregard.single,
            ],
            default=0,
        )
