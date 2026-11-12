from collections import Counter

import pytest

from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    CLAIMANT_OR_PARTNER_BENEFITS,
    FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.universal_credit.benefit_cap.uc_benefit_cap_welfare_benefits import (
    UC_FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    FAMILY_GROSS_INCOME_BENEFITS,
)


@pytest.mark.parametrize(
    "names",
    [
        CLAIMANT_OR_PARTNER_BENEFITS + FAMILY_BENEFITS,
        CLAIMANT_OR_PARTNER_BENEFITS + UC_FAMILY_BENEFITS,
        FAMILY_GROSS_INCOME_BENEFITS,
    ],
    ids=["housing-benefit-cap", "universal-credit-cap", "non-dependant-family-income"],
)
def test_each_name_occurs_once(names):
    assert not {name: n for name, n in Counter(names).items() if n != 1}
