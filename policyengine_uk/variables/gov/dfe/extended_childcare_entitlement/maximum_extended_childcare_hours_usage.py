from policyengine_uk.model_api import *


class maximum_extended_childcare_hours_usage(Variable):
    value_type = float
    entity = BenUnit
    label = "maximum extended childcare hours used"
    documentation = (
        "The maximum number of weekly funded childcare hours this family uses "
        "for each child once eligible for the extended (working parent) "
        "entitlement. It caps the child's total funded hours, universal or "
        "targeted hours included. Those hours are never reduced below their "
        "own value, so for a child who gets them a limit under 15 adds no "
        "working parent hours rather than removing universal or targeted "
        "ones; a child without them, such as a 1-year-old, gets working "
        "parent hours up to the limit."
    )
    definition_period = YEAR
    default_value = 30  # By default, uses up to 30 hours per week
