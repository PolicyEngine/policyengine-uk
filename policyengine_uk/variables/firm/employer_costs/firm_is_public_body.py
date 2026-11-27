from policyengine_uk.model_api import *


class firm_is_public_body(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is a public authority"
    documentation = (
        "Whether the firm is a public authority, including a body whose "
        "activities are mainly of a public nature. A public authority that is "
        "not a charity cannot claim the Employment Allowance."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.2",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/2",
        ),
    ]
