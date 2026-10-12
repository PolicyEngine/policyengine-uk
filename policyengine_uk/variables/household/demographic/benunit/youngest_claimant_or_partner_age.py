from policyengine_uk.model_api import *


class youngest_claimant_or_partner_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Age of the younger of the claimant and partner"
    documentation = (
        "The age of the claimant, or of the younger member of a couple. "
        "Children and young persons in the family do not count. Infinity if "
        "the benefit unit has no claimant."
    )
    definition_period = YEAR
    unit = "year"

    def formula(benunit, period, parameters):
        person = benunit.members
        return benunit.min(
            where(
                person("is_claimant_or_partner", period),
                person("age", period),
                np.inf,
            )
        )
