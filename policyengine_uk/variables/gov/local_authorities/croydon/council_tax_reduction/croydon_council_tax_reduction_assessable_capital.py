from policyengine_uk.model_api import *


class croydon_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Croydon Council Tax Support assessable capital"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.croydon.gov.uk/benefits/changes-council-tax-support/your-capital-savings-investments-and-property"

    def formula(benunit, period, parameters):
        has_uc = benunit("universal_credit", period) > 0
        return where(
            has_uc,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
