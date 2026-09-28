from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = (
        "Whether a claimant or partner meets the modelled minimum-age and "
        "pension-age conditions and the benefit unit meets the capital limit. "
        "One qualifying claimant suffices, preserving mixed-age couples under "
        "regulation 3(2)(a). Dependants cannot satisfy the claimant age test."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/3",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
    )

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        claimant = benunit.members("is_uc_claimant", period)
        meets_minimum_age = benunit.members("meets_uc_minimum_age_condition", period)
        pension_age = benunit.members("is_SP_age", period)
        has_qualifying_claimant = benunit.any(
            claimant & meets_minimum_age & ~pension_age
        )
        return has_qualifying_claimant & (capital <= limit)
