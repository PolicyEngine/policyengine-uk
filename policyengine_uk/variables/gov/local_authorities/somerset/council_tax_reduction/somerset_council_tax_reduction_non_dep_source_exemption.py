from policyengine_uk.model_api import *


class somerset_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Somerset CTR non-dependant is source-excluded from the deduction"
    definition_period = YEAR
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"
