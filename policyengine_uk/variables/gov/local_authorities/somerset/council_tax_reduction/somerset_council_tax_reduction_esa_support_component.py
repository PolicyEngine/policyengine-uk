from policyengine_uk.model_api import *


class somerset_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = "Somerset CTR annual ESA support component amount to disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"
