from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_countable_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Buckinghamshire Council Tax Reduction countable Universal Credit income"
    definition_period = YEAR
    unit = GBP
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        award = benunit("universal_credit", period)
        disregarded_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_LCWRA_element",
                "uc_individual_disabled_child_element",
                "uc_individual_severely_disabled_child_element",
                "uc_carer_element",
            ],
        )
        disregarded_elements += benunit(
            "buckinghamshire_council_tax_reduction_source_disregarded_uc_elements",
            period,
        )
        return has_uc_award * max_(0, award - disregarded_elements)
