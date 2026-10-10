from policyengine_uk.model_api import *
from policyengine_core.variables import Variable
from policyengine_uk.utils.marginal_rates import marginal_rate_step


class marginal_tax_rate(Variable):
    label = "Marginal tax rate"
    documentation = (
        "Percent of marginal income gains that do not increase household net "
        "income. The marginal income is gov.simulation.marginal_tax_rate_delta, "
        "or 0.1% of employment income where that is larger, and the rise in net "
        "income is divided by the rise in employment income as stored, so that "
        "float32 rounding stays negligible at any level of earnings."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(person, period, parameters):
        p = parameters(period).gov.simulation
        mtr_values = np.zeros(person.count, dtype=np.float32)
        simulation = person.simulation
        adult_index_values = person("adult_index", period)
        employment_income = person("employment_income", period)
        step = marginal_rate_step(employment_income, p.marginal_tax_rate_delta)
        adult_count = p.marginal_tax_rate_adults
        for adult_index in range(1, 1 + adult_count):
            alt_simulation = simulation.get_branch(f"adult_{adult_index}_pay_rise")
            mask = adult_index_values == adult_index
            for variable in simulation.tax_benefit_system.variables:
                variable_data = simulation.tax_benefit_system.variables[variable]
                if (
                    variable not in simulation.input_variables
                    and not variable_data.is_input_variable()
                ):
                    alt_simulation.delete_arrays(variable)
            alt_simulation.set_input(
                "employment_income",
                period,
                employment_income + mask * step,
            )
            alt_person = alt_simulation.person
            # Float32 rounds the higher earnings, so divide by the rise stored.
            pay_rise = alt_person("employment_income", period) - employment_income
            household_net_income = person.household("household_net_income", period)
            household_net_income_higher_earnings = alt_person.household(
                "household_net_income", period
            )
            increase = household_net_income_higher_earnings - household_net_income
            mtr_values += where(mask, 1 - increase / where(mask, pay_rise, 1), 0)
        return mtr_values
