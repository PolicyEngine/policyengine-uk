from policyengine_uk.model_api import *


class is_engaged_in_owned_company_trade(Variable):
    value_type = bool
    entity = Person
    label = "engaged in the trade of an owned company"
    documentation = (
        "Whether the person is engaged in activities in the course of the "
        "trade of the company in which they stand as sole owner or partner. "
        "DWP guidance treats any work for the company, however little (such "
        "as taking its telephone messages), as engagement."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(3)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, para. H4373",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]
