from policyengine_uk.model_api import *


class owned_company_carries_on_property_business(Variable):
    value_type = bool
    entity = Person
    label = "owned company carries on a property business"
    documentation = (
        "Whether the company in which the person stands as sole owner or "
        "partner carries on a property business within the meaning of section "
        "204 of the Corporation Tax Act 2009, such as letting land or "
        "buildings it owns as an investment."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(1) and (6)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Corporation Tax Act 2009 s. 204",
            href="https://www.legislation.gov.uk/ukpga/2009/4/section/204",
        ),
    ]
