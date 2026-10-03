from policyengine_uk.model_api import *


class rent_a_room_income_tax(Variable):
    value_type = float
    entity = Person
    label = "income tax on rent-a-room income"
    documentation = (
        "The share of income tax on property income that falls on taxable "
        "rent-a-room income, in proportion to its share of taxable property "
        "income. The legacy means tests count rent-a-room receipts as income "
        "and disregard the tax paid on income they count."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        taxable_rent_a_room = person("taxable_rent_a_room_income", period)
        taxable_property = person("taxable_property_income", period)
        share = np.divide(
            taxable_rent_a_room,
            taxable_property,
            out=np.zeros_like(taxable_property),
            where=taxable_property > 0,
        )
        return person("property_income_tax", period) * share
