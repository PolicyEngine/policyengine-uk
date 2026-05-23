from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_north_northamptonshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class north_northamptonshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether the benefit unit is under North Northamptonshire's local CTR scheme"
    )
    definition_period = YEAR
    reference = "https://northnorthants.moderngov.co.uk/documents/s34359/Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        return (
            (country == Country.ENGLAND)
            & is_north_northamptonshire(local_authority)
            & ~has_pensioner
        )
