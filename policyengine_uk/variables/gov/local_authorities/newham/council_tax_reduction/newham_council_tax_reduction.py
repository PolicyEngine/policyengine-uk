from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_newham_working_age,
)


class newham_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Newham Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.newham.council_tax_reduction
        household = benunit.household
        working_age = is_newham_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "newham_council_tax_reduction_non_dep_deductions",
        )
