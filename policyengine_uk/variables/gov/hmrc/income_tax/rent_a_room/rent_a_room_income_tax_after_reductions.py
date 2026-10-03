from policyengine_uk.model_api import *


class rent_a_room_income_tax_after_reductions(Variable):
    value_type = float
    entity = Person
    label = "income tax on rent-a-room income after tax reductions"
    documentation = (
        "The tax on taxable rent-a-room income less its share of the Step 6 "
        "tax reductions, shared in proportion to the Step 4 tax on each kind "
        "of income as legacy_means_test_income_tax does. It is the part of "
        "income tax paid on this rent, which programmes that do not count the "
        "rent must not deduct from the income they do count."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/23"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax
        rent_a_room_tax = person("rent_a_room_income_tax", period)
        before_reductions = add(
            person,
            period,
            [
                "earned_income_tax",
                "savings_income_tax",
                "dividend_income_tax",
                "property_income_tax",
            ],
        )
        reductions = min_(
            add(person, period, p.income_tax_subtractions), before_reductions
        )
        share = np.divide(
            rent_a_room_tax,
            before_reductions,
            out=np.zeros_like(rent_a_room_tax, dtype=float),
            where=before_reductions > 0,
        )
        return rent_a_room_tax - reductions * share
