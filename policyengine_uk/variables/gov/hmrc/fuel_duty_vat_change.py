from policyengine_uk.model_api import *
from policyengine_uk.utils.parameters import fiscal_year_average


def _baseline_rate(parameter, year):
    value = (
        fiscal_year_average(parameter, year)
        if (parameter.metadata or {}).get("fiscal_year_blend", False)
        else None
    )
    return parameter(f"{year}-04-30") if value is None else value


class fuel_duty_vat_change(Variable):
    label = "VAT change from road fuel duty"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.gov.uk/hmrc-internal-manuals/vat-valuation/vatval02300",
        "https://obr.uk/forecasts-in-depth/tax-by-tax-spend-by-spend/fuel-duties/",
    )

    def formula_2015(household, period, parameters):
        p = parameters(period).gov.hmrc
        current = p.fuel_duty
        # The unreformed tree keeps statutory dates, unlike the annualised
        # current tree. Apply the same fiscal conversion to each baseline rate.
        baseline = household.simulation.tax_benefit_system.parameters.baseline.gov.hmrc.fuel_duty
        rates = {
            name: _baseline_rate(getattr(baseline, name), period.start.year)
            for name in (
                "petrol_and_diesel",
                "rural_fuel_duty_relief",
                "lpg",
                "natural_gas",
            )
        }
        relief_area = household("in_rural_fuel_duty_relief_area", period)
        rate_change = (
            current.petrol_and_diesel
            - rates["petrol_and_diesel"]
            - relief_area
            * (current.rural_fuel_duty_relief - rates["rural_fuel_duty_relief"])
        )
        duty_change = (
            add(household, period, ["petrol_litres", "diesel_litres"]) * rate_change
            + household("lpg_kg", period) * (current.lpg - rates["lpg"])
            + household("natural_gas_kg", period)
            * (current.natural_gas - rates["natural_gas"])
        )
        return duty_change * p.vat.standard_rate
