from policyengine_uk.model_api import *


class somerset_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Somerset CTR treats a pension-age Universal Credit award as within the "
        "Universal Credit Transitional Provisions regulation 60A relevant period"
    )
    definition_period = YEAR
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"
