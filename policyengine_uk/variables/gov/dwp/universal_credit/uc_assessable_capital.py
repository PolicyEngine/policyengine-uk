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
        p = parameters(period).gov.dwp.universal_credit.means_test
        sources = p.capital.sources
        capital_derived_income = add(
            benunit,
            period,
            p.income_definitions.capital_derived,
        )
        household_capital = add(household, period, sources)
        single_benunit_household = household("household_num_benunits", period) == 1
        household_head_benunit = benunit.any(
            benunit.members("is_household_head", period)
        )
        reported_capital = benunit("uc_reported_capital", period)
        use_reported_capital = reported_capital > 0
        household_capital_proxy = household_capital + capital_derived_income
        assessed_capital = where(
            use_reported_capital,
            reported_capital,
            where(
                single_benunit_household | household_head_benunit,
                household_capital_proxy,
                0,
            ),
        )
        return max_(0, assessed_capital)
