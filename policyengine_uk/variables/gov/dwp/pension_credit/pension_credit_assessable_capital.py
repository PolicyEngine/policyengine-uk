from policyengine_uk.model_api import *


class pension_credit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension Credit assessable capital"
    documentation = (
        "Pension Credit capital counted from the configured capital sources, "
        "assigned in full to pension-age benunits because the dataset stores "
        "capital at household level and does not distinguish ownership across "
        "separate adult benunits."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        p = parameters(period).gov.dwp.pension_credit.income.capital
        household_capital = add(household, period, p.sources)
        any_pension_age = benunit.any(person("is_SP_age", period))
        return where(any_pension_age, max_(0, household_capital), 0)
