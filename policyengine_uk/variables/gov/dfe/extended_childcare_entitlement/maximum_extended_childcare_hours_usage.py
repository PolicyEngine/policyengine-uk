from policyengine_uk.model_api import *


class maximum_extended_childcare_hours_usage(Variable):
    value_type = float
    entity = BenUnit
    label = "maximum extended childcare hours used"
    documentation = (
        "The maximum number of weekly funded childcare hours this family uses "
        "for each child once eligible for the extended (working parent) "
        "entitlement. It caps the child's total funded hours, universal or "
        "targeted hours included; those hours are never reduced below their "
        "own value, so a limit under 15 adds no working parent hours rather "
        "than removing universal or targeted ones."
    )
    definition_period = YEAR
    default_value = 30  # By default, uses up to 30 hours per week
