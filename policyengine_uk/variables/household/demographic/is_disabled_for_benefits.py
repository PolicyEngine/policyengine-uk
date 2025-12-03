from policyengine_uk.model_api import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a disability"
    documentation = (
        "Whether this person is disabled for benefits purposes. "
        "In dataset mode, determined by reported DLA/PIP claims."
    )
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False
