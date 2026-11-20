from policyengine_uk.model_api import *


class has_company_car(Variable):
    value_type = bool
    entity = Person
    label = "Has a company car"
    documentation = (
        "Whether the person has a company car available for private use, "
        "which the model takes from a positive company_car_list_price. The "
        "appropriate percentage and the company car and car fuel benefits "
        "are zero without one."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 s. 114",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/114",
    )

    def formula(person, period, parameters):
        return person("company_car_list_price", period) > 0
