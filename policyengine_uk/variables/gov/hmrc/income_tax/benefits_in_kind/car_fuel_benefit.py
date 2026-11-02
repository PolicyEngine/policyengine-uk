from policyengine_uk.model_api import *
from policyengine_uk.utils.company_car import (
    co2_emissions_figure,
    share_of_year_available,
)


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
    defined_for = "has_company_car"
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
        fuel_provided = person("company_car_private_fuel_provided", period)
        # s. 149(4): the same test as the zero-emission rate in s. 139.
        can_emit_co2 = co2_emissions_figure(person, period) > 0
        full_year = p.multiplier * person("company_car_appropriate_percentage", period)
        availability = share_of_year_available(person, period)
        return fuel_provided * can_emit_co2 * full_year * availability
