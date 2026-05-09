from policyengine_uk.model_api import *


class bath_and_north_east_somerset_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the Bath and North East Somerset CTR claimant is in the protected 100 percent support and 16,000 pound capital-limit group"
    definition_period = YEAR
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"
    documentation = (
        "Source input for cases where the applicant or partner receives the ESA "
        "support component, enhanced disability premium, enhanced disability "
        "premium for dependants, disability child premium, or severe disability premium."
    )
