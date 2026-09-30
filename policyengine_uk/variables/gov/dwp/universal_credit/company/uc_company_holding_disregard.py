from policyengine_uk.model_api import *


class uc_company_holding_disregard(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit disregard of a holding in an owned company"
    documentation = (
        "The value of the person's holding in the company in which they stand "
        "as sole owner or partner, which Universal Credit disregards; the "
        "company's own capital is counted instead (uc_company_capital)."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(2)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )

    def formula(person, period, parameters):
        return where(
            person("uc_company_owner_treatment_applies", period),
            person("owned_company_holding_value", period),
            0,
        )
