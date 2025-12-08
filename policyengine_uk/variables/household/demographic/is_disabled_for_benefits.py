from policyengine_uk.model_api import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a disability"
    documentation = "Whether this person is disabled for benefits purposes"
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "dla",
            "pip",
        ]

        p_claims_lcwra_if_on_pip_dla = 0.8
        p_claims_lcwra_if_not_on_pip_dla = 0.13

        random_seed = random(person)

        on_qual_benefits = add(person, period, QUALIFYING_BENEFITS) > 0

        return np.where(
            on_qual_benefits,
            random_seed < p_claims_lcwra_if_on_pip_dla,
            random_seed < p_claims_lcwra_if_not_on_pip_dla,
        )
