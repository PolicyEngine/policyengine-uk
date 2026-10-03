from policyengine_uk.model_api import *


class uc_startup_period_barred_by_earlier_floor_or_startup(Variable):
    value_type = bool
    entity = Person
    label = (
        "Universal Credit start-up period barred by an earlier floor or start-up period"
    )
    documentation = (
        "Whether the claimant's history bars a new start-up period: the "
        "minimum income floor has applied to them before in relation to "
        "their current trade, on this award or an earlier one, or a start-up "
        "period has applied to them before, unless that one began more than "
        "5 years earlier and was for a different trade they have since "
        "ceased. Surveys do not record this history, so it defaults to "
        "false: the model takes a claimant found to be in gainful "
        "self-employment for the first time to be eligible. Set it for a "
        "claimant whose floor or start-up period is known."
    )
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 63(1)(a) and (2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/63",
        ),
    ]
    definition_period = YEAR
    default_value = False
