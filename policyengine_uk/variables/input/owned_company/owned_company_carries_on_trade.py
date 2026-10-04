from policyengine_uk.model_api import *


class owned_company_carries_on_trade(Variable):
    value_type = bool
    entity = Person
    label = "owned company carries on a trade"
    documentation = (
        "Whether the company in which the person stands as sole owner or "
        "partner carries on a trade: a business with a profit-seeking motive, "
        "usually providing goods or services to customers on a commercial "
        "basis."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(1) and (3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, para. H4370",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]
