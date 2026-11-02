from policyengine_uk.model_api import *


class would_evade_tv_licence_fee(Variable):
    label = "Would evade TV licence fee"
    documentation = (
        "Whether this household would unlawfully evade the TV licence fee. "
        "Generated stochastically in the dataset using evasion rates. The "
        "realised result does not change in response to reforms of the fee."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False
