from policyengine_uk.model_api import *
from policyengine_uk.utils.legacy_means_test_tax import legacy_means_test_tax_split


class rent_a_room_income_tax_after_reductions(Variable):
    value_type = float
    entity = Person
    label = "income tax on rent-a-room income after tax reductions"
    documentation = (
        "The tax on taxable rent-a-room income less its share of the Step 6 "
        "tax reductions (income_tax_reductions). The formula shares the "
        "reductions as legacy_means_test_income_tax does: the residential "
        "finance-cost reduction comes off the property income tax on income "
        "from capital first, and the formula shares the rest in proportion "
        "to the Step 4 tax left on each kind of income. For a person whose "
        "only counted income is taxable rent-a-room income, the two give the "
        "same figure. rent_a_room_income_tax_without_earnings reads it to "
        "find the tax on rent that a council tax reduction scheme does not "
        "count."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/27",
    ]

    def formula(person, period, parameters):
        return legacy_means_test_tax_split(person, period)[
            "rent_a_room_after_reductions"
        ]
