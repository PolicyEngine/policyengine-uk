from policyengine_uk.model_api import *
from policyengine_uk.utils.company_car import co2_emissions_figure


class company_car_appropriate_percentage(Variable):
    value_type = float
    entity = Person
    label = "Appropriate percentage of the person's company car"
    documentation = (
        "The share of the company car's price taxed each year as its "
        "benefit, which the car fuel benefit also uses (ITEPA 2003 s. 139). "
        "A car emitting 0 g/km takes the zero-emission rate, one emitting 1 "
        "to 50 g/km a rate by its electric range, and one emitting 51 to "
        "74 g/km a rate from the table. From 75 g/km the rate is the base "
        "rate plus one point for each full 5 g/km above 75, up to the "
        "maximum. A car of the ELECTRIC fuel type is taken to emit 0 g/km. "
        "A diesel car not meeting the Euro 6d (RDE2) standard adds the "
        "diesel supplement, within the maximum (s. 141). In 2020-21 and "
        "2021-22 a car first registered on or after 6 April 2020 takes the "
        "s. 139A rates. Zero for a person without a company car. Cars "
        "without a CO2 emissions figure (s. 140) and cars first registered "
        "before 1 January 1998 (s. 142) are not modelled. Calculated from "
        "2020-21."
    )
    definition_period = YEAR
    unit = "/1"
    defined_for = "has_company_car"
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 139",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/139",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 141",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/141",
        ),
        dict(
            title="Finance Act 2020 ss. 9 and 10 (s. 139A for 2020-21 and 2021-22)",
            href="https://www.legislation.gov.uk/ukpga/2020/14/section/9/enacted",
        ),
    ]

    def formula_2020(person, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.income_tax.benefits_in_kind.company_car.appropriate_percentage
        # s. 139(2): the CO2 emissions figure is rounded down to a whole
        # number and the electric range figure up.
        co2 = co2_emissions_figure(person, period)
        electric_range = np.ceil(max_(person("company_car_electric_range", period), 0))
        from_april_2020 = p.registered_from_6_april_2020
        takes_s139a_rates = from_april_2020.in_effect & person(
            "company_car_registered_from_6_april_2020", period
        )
        electric_range_rate = where(
            takes_s139a_rates,
            from_april_2020.electric_range.calc(electric_range),
            p.electric_range.calc(electric_range),
        )
        co2_band_rate = where(
            takes_s139a_rates,
            from_april_2020.co2_band.calc(co2),
            p.co2_band.calc(co2),
        )
        # s. 139(3) and (4): from the threshold, the base rate plus the
        # increment for each full step above it, up to the maximum.
        graduated = p.graduated
        base_rate = where(
            takes_s139a_rates,
            from_april_2020.graduated_base_rate,
            graduated.base_rate,
        )
        steps = np.floor((co2 - graduated.threshold) / graduated.step)
        graduated_rate = min_(
            base_rate + graduated.increment * max_(steps, 0), p.maximum
        )
        # Finance Act 2020 ss. 9(2)(a) and 10(2)(a) give the s. 139 table the
        # s. 139A rate for 0 g/km, so both schedules use the one
        # zero-emission rate.
        zero_emission = co2 == 0
        rate = select(
            [
                zero_emission,
                co2 <= p.electric_range_co2_limit,
                co2 < graduated.threshold,
            ],
            [p.zero_emission, electric_range_rate, co2_band_rate],
            default=graduated_rate,
        )
        # s. 141: a diesel car not meeting the Euro 6d standard adds the
        # supplement, up to the maximum. A car that cannot emit CO2 is not
        # propelled by diesel (s. 141(3)).
        fuel_type = person("company_car_fuel_type", period)
        diesel = (fuel_type == fuel_type.possible_values.DIESEL_NON_RDE2) & ~(
            zero_emission
        )
        return where(diesel, min_(rate + p.diesel_supplement, p.maximum), rate)
