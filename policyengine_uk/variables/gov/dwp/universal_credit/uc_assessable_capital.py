from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Universal Credit capital counted from the configured household asset "
        "sources under the current model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        household = benunit.household
        sources = parameters(period).gov.dwp.universal_credit.means_test.capital.sources
        total_capital = add(household, period, sources)
        num_benunits = max_(1, household("household_num_benunits", period))
        return max_(0, total_capital / num_benunits)
