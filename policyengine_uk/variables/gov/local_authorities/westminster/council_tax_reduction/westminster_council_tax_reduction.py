from policyengine_uk.model_api import *
import numpy as np
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_westminster_working_age,
)


class westminster_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Westminster Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.westminster.council_tax_reduction
        household = benunit.household
        working_age = is_westminster_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        has_uc_award = benunit("universal_credit", period) > 0
        capital = household("savings", period)
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_step
        )
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "westminster_council_tax_reduction_non_dep_deductions",
            additional_applicable_income=where(
                has_uc_award,
                0,
                weekly_tariff_income * WEEKS_IN_YEAR,
            ),
        )
