from policyengine_uk.model_api import *


class household_owns_tv(Variable):
    label = "Owns a TV"
    documentation = (
        "Whether this household owns a functioning colour TV. "
        "Generated stochastically in the dataset using TV ownership rates."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True
