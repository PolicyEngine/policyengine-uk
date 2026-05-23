from policyengine_uk.model_api import *
import numpy as np
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_greenwich_working_age,
)


class greenwich_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Greenwich Local Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.greenwich.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_greenwich_working_age(local_authority, country, has_pensioner)
        capital = benunit.household("savings", period)
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_step
        )
        has_uc = benunit("universal_credit", period) > 0
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "greenwich_council_tax_reduction_non_dep_deductions",
            additional_applicable_income=where(
                has_uc, 0, weekly_tariff_income * WEEKS_IN_YEAR
            ),
        )
