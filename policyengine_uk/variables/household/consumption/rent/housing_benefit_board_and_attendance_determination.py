from policyengine_uk.model_api import *


class housing_benefit_board_and_attendance_determination(Variable):
    value_type = bool
    entity = BenUnit
    label = "Rent officer found the rent substantially for board and attendance"
    documentation = (
        "Whether a rent officer has determined that a substantial part of the "
        "family's rent is fairly attributable to board and attendance. Housing "
        "Benefit then leaves the Local Housing Allowance for a rent officer "
        "determination, from which the fixed amount for meals is deducted. "
        "Knowing that the rent includes meals does not by itself establish "
        "this."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13C",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
    )
