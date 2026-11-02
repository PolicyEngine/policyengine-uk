from policyengine_uk.model_api import *


class child_limit_adoption_exception(Variable):
    value_type = bool
    entity = Person
    label = "Two-child limit adoption exception"
    documentation = (
        "Whether the adoption exception to the Universal Credit and Child Tax "
        "Credit child limit applies to this child or qualifying young person: "
        "the child was placed for adoption with, or adopted by, the claimant "
        "under UK adoption law, and the claimant was not the child's "
        "step-parent immediately before the adoption or a parent other than by "
        "adoption, and it was not a Convention or overseas adoption."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/paragraph/3/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/11/2025-04-06",
    )
