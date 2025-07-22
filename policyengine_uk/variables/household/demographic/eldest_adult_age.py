from policyengine_uk.model_api import *


class eldest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(
            where(
                benunit.members("is_adult", period),
                benunit.members("age", period),
                -np.inf,
            )
        )
