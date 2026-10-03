from policyengine_uk.model_api import *


class eldest_claimant_or_partner_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Age of the elder of the claimant and partner"
    documentation = (
        "The age of the claimant, or of the older member of a couple. "
        "Children and young persons in the family do not count. Negative "
        "infinity if the benefit unit has no claimant."
    )
    definition_period = YEAR
    unit = "year"

    def formula(benunit, period, parameters):
        person = benunit.members
        return benunit.max(
            where(
                person("is_claimant_or_partner", period),
                person("age", period),
                -np.inf,
            )
        )
