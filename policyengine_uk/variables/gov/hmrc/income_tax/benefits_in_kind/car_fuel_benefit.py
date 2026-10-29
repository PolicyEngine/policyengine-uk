from policyengine_uk.model_api import *


class car_fuel_benefit(Variable):
    value_type = float
    entity = Person
    label = "Car fuel benefit"
    documentation = (
        "The cash equivalent of fuel provided for private use of the "
        "person's company car, treated as earnings from their employment "
        "(ITEPA 2003 s. 149): the car's appropriate percentage of the car "
        "fuel benefit charge multiplier (s. 150), reduced in proportion to "
        "the days the car is unavailable (s. 152(1)). It is nil where the "
        "person makes good the whole cost of private fuel (s. 151), and for "
        "a car that cannot emit CO2, whose energy is not fuel (s. 149(4)). "
        "Payments for private use and capital contributions do not reduce "
        "it. Calculated from 2020-21."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 149",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/149",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 150",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/150",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 152",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/152",
        ),
        dict(
            title="HMRC 480 Chapter 13: taxable fuel provided for company cars and vans",
            href="https://www.gov.uk/guidance/taxable-fuel-provided-for-company-cars-and-vans-480-chapter-13",
        ),
    ]

    def formula_2020(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.benefits_in_kind.car_fuel
        has_company_car = person("company_car_list_price", period) > 0
        fuel_provided = person("company_car_private_fuel_provided", period)
        can_emit_co2 = person("company_car_co2_emissions", period) > 0
        full_year = p.multiplier * person("company_car_appropriate_percentage", period)
        availability = min_(max_(person("company_car_availability", period), 0), 1)
        return has_company_car * fuel_provided * can_emit_co2 * full_year * availability
