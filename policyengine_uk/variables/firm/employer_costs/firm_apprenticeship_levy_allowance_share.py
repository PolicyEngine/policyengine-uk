from policyengine_uk.model_api import *


class firm_apprenticeship_levy_allowance_share(Variable):
    value_type = float
    entity = Firm
    label = "Firm share of the apprenticeship levy allowance"
    documentation = (
        "Share of the levy allowance allocated to the firm. Connected "
        "companies form a company unit whose members share one allowance and "
        "choose each member's part; the shares sum to one across the unit. 1 "
        "for a firm with no connected companies."
    )
    definition_period = YEAR
    unit = "/1"
    default_value = 1
    reference = [
        dict(
            title="Finance Act 2016 s.101",
            href="https://www.legislation.gov.uk/ukpga/2016/24/section/101",
        ),
    ]
