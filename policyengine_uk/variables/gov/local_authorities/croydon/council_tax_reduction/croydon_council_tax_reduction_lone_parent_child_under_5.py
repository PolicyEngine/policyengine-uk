from policyengine_uk.model_api import *


class croydon_council_tax_reduction_lone_parent_child_under_5(Variable):
    value_type = bool
    entity = BenUnit
    label = "Croydon Council Tax Support lone parent with a child under 5"
    definition_period = YEAR
    reference = "https://www.croydon.gov.uk/benefits/changes-council-tax-support/how-we-work-out-amount-council-tax-support"

    def formula(benunit, period, parameters):
        return benunit("is_lone_parent", period) & (
            benunit("youngest_child_age", period) < 5
        )
