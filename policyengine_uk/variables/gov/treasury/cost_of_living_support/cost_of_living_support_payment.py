from policyengine_uk.model_api import *


class cost_of_living_support_payment(Variable):
    label = "Cost-of-living support payment"
    documentation = (
        "The household's Cost of Living Payments in the year: the "
        "means-tested payment to each of its benefit units, the disability "
        "payment to each of its members and the pensioner payment, once per "
        "household with a Winter Fuel Payment."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2022/38/section/1",
        "https://www.legislation.gov.uk/ukpga/2022/38/section/5",
        "https://www.legislation.gov.uk/ukpga/2023/7/section/1",
        "https://www.legislation.gov.uk/ukpga/2023/7/section/5",
        "https://www.gov.uk/guidance/cost-of-living-payment-pensioner",
    ]

    def formula(household, period, parameters):
        pensioners = parameters(period).gov.treasury.cost_of_living_support.pensioners
        unit_and_person_payments = add(
            household,
            period,
            [
                "cost_of_living_means_tested_payment",
                "cost_of_living_disability_payment",
            ],
        )
        on_pensioner_benefit = (
            add(household, period, pensioners.qualifying_benefits) > 0
        )
        return unit_and_person_payments + pensioners.amount * on_pensioner_benefit
