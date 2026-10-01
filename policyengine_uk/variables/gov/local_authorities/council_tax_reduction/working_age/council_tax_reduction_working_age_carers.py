from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_carers(Variable):
    value_type = int
    entity = BenUnit
    label = "Claimants and partners qualifying for the working-age CTR carer premium"
    documentation = (
        "The number of claimants and partners who receive Carer's Allowance "
        "or, in Scotland, Carer Support Payment. In Scotland an award of "
        "Universal Credit with the carer element also qualifies; when no one "
        "in the family receives a carer benefit, it counts as one carer."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/14",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        receives = person("receives_carer_benefit", period)
        carers = benunit.sum(claimant_or_partner & receives)
        scotland = is_scotland_scheme(benunit.household("country", period))
        uc_carer_element = benunit("uc_carer_element", period) > 0
        return carers + (scotland & uc_carer_element & (carers == 0))
