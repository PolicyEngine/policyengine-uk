from policyengine_uk.model_api import *


class benunit_contains_household_head(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit contains the household head"
    documentation = (
        "Whether the household head (see is_resolved_household_head) is in "
        "this family, so exactly one family in each household contains it "
        "whatever is_household_head flags. Rent liability, Universal Credit "
        "and Housing Benefit non-dependants and size criteria, boarders and "
        "lodgers, and the Council Tax Reduction claimant all read this "
        "family as the household head's."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("is_resolved_household_head", period))
