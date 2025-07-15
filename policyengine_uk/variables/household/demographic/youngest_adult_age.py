from policyengine_uk.model_api import *


class youngest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            where(
                benunit.members("is_adult", period),
                benunit.members("age", period),
                np.inf,
            )
        )
