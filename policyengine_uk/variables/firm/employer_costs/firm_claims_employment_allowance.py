from policyengine_uk.model_api import *


class firm_claims_employment_allowance(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is the group member that claims the Employment Allowance"
    documentation = (
        "Whether the firm is the member of its group of connected companies "
        "or charities that the group chooses to claim the Employment "
        "Allowance. Only one member of a connected group may claim. True for "
        "a firm with no connected companies."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = True
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.3",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/3",
        ),
    ]
