from policyengine_uk.model_api import *


class croydon_council_tax_reduction_countable_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Croydon Council Tax Support countable Universal Credit income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.croydon.gov.uk/benefits/changes-council-tax-support/example-support-calculations"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.croydon.council_tax_reduction
        ignored_elements = (
            add(
                benunit,
                period,
                [
                    "uc_housing_costs_element",
                    "uc_LCWRA_element",
                    "uc_individual_disabled_child_element",
                    "uc_individual_severely_disabled_child_element",
                ],
            )
            + benunit("uc_carer_element", period)
            * ctr.universal_credit.ignored_carer_element_rate
        )
        has_uc = benunit("universal_credit", period) > 0
        return has_uc * max_(0, benunit("universal_credit", period) - ignored_elements)
