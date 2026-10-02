from policyengine_uk.model_api import *


class youngest_child_age_for_legacy_benefits(Variable):
    value_type = float
    entity = BenUnit
    label = "Age of youngest child for legacy means-tested benefits"
    documentation = (
        "Youngest family member under 16, excluding the claimant and partner. "
        "SSCBA sections 137(1) and 142(1) use the same child age definition. "
        "Infinity if the benefit unit contains no such child."
    )
    definition_period = YEAR
    unit = "year"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        child = person("is_child_for_child_benefit", period) & ~person(
            "is_claimant_or_partner", period
        )
        return benunit.min(where(child, person("age", period), np.inf))
