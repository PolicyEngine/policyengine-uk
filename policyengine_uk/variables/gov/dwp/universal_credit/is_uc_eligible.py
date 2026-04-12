from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = "Whether this family is eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        capital_limit = parameters(
            period
        ).gov.dwp.universal_credit.means_test.capital.capital_limit
        has_working_age_adult = benunit.any(benunit.members("is_WA_adult", period))
        return has_working_age_adult & (capital <= capital_limit)
