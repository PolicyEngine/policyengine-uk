from policyengine_uk.model_api import *


class taxable_property_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Property income for Income Tax after allowances"
    documentation = (
        "Taxable property income less the part of the allowances it absorbs. "
        "Allowances go to non-savings, non-dividend income first, and "
        "property income is stacked above the rest of it, so it takes "
        "whatever allowances the other non-savings income leaves. From "
        "2027-28 that order is statutory: s. 25(3A) sets allowances against "
        "income other than property, savings and dividend income first, and "
        "s. 16A places property income immediately below savings income."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007, s. 25(3A) (from 2027-28)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
        ),
        dict(
            title="Income Tax Act 2007, s. 16A (from 2027-28)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/16A",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        non_savings_after_allowances = person(
            "non_savings_income_after_allowances", period
        )
        return min_(
            person("taxable_property_income", period), non_savings_after_allowances
        )
