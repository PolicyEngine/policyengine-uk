from policyengine_uk.model_api import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a disability"
    documentation = "Whether this person is disabled for benefits purposes"
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        # In microsimulation, this is set in the dataset (see frs.py line 726)
        # This formula only runs for policy calculator (non-dataset)

        # Deterministic rule: disabled if they receive qualifying benefits
        QUALIFYING_BENEFITS = [
            "dla",
            "pip",
        ]

        on_qual_benefits = add(person, period, QUALIFYING_BENEFITS) > 0
        return on_qual_benefits
