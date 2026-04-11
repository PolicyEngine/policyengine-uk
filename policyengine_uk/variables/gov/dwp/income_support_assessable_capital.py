from policyengine_uk.model_api import *


class income_support_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for Income Support"
    documentation = (
        "Household capital apportioned to the benefit unit for the Income Support "
        "capital test."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        sources = IS.means_test.capital.sources

        # The data model stores these capital stocks at household level, so split
        # them across the benefit units in the household as a pragmatic proxy.
        household_capital = sum(
            benunit.max(benunit.members.household(source, period)) for source in sources
        )
        household_num_benunits = benunit.max(
            benunit.members.household("household_num_benunits", period)
        )
        return household_capital / max_(1, household_num_benunits)
