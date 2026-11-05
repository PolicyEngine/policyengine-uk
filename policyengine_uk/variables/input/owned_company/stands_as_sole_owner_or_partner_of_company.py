from policyengine_uk.model_api import *


class stands_as_sole_owner_or_partner_of_company(Variable):
    value_type = bool
    entity = Person
    label = "stands as sole owner or partner of a company"
    documentation = (
        "Whether the person stands in a position analogous to that of a sole "
        "owner or partner in relation to a company. This is a question of "
        "fact. DWP guidance treats a person as like a sole owner when they "
        "have total influence over the day-to-day running of the company (for "
        "example owning 99% of the shares), and as like a partner when the "
        "company has a small number of shareholders and the person has some "
        "meaningful influence over its day-to-day running. A shareholder in a "
        "company with many shareholders is an investor, not an owner or "
        "partner. The person need not work for the company."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, paras. H4362-H4364",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]
