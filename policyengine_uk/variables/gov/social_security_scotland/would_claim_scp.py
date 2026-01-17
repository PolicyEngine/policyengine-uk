from policyengine_uk.model_api import *


class would_claim_scp(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Scottish Child Payment for this child"
    documentation = (
        "Whether this child would be claimed for under Scottish Child Payment. "
        "Generated stochastically in the dataset using age-based take-up rates: "
        "97% for children under 6, 85% for children 6+. "
        "Source: gov.scot take-up rates publication Nov 2024."
    )
    definition_period = YEAR
    reference = "https://www.gov.scot/publications/take-up-rates-scottish-benefits-2024/pages/3/"

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True
