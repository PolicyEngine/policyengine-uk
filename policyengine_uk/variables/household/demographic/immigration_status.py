from policyengine_uk.model_api import *


class ImmigrationStatus(Enum):
    CITIZEN = "UK citizen"
    SETTLED = "Settled status (indefinite leave to remain)"
    PRE_SETTLED = "Pre-settled status (limited leave to remain)"
    REFUGEE = "Refugee"
    HUMANITARIAN_PROTECTION = "Humanitarian protection"
    DISCRETIONARY_LEAVE = "Discretionary leave to remain"
    VISA_HOLDER = "Visa holder (subject to immigration control)"
    OTHER = "Other"


class immigration_status(Variable):
    value_type = Enum
    possible_values = ImmigrationStatus
    default_value = ImmigrationStatus.CITIZEN
    entity = Person
    label = "Immigration status"
    documentation = (
        "The person's immigration status in the UK, used to determine "
        "eligibility for benefits under immigration control rules"
    )
    definition_period = YEAR
