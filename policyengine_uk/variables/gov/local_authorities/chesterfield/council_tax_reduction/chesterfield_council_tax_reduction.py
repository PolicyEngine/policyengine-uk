from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_chesterfield_working_age,
)


class chesterfield_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Chesterfield Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.chesterfield.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_chesterfield_working_age(
            local_authority, country, has_pensioner
        )
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "chesterfield_council_tax_reduction_non_dep_deductions",
        )
