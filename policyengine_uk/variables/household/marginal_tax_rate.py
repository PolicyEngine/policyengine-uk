from policyengine_uk.model_api import *
from policyengine_core.variables import Variable
from policyengine_uk.utils.marginal_rates import marginal_rate_step
from policyengine_uk.utils.measurement_branches import (
    held_behavioural_responses,
    hold_behavioural_responses,
    retained_input_variables,
)


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
        # The pay rise is not a reform: each branch holds the behavioural
        # responses (labour supply and realised gains) at this simulation's
        # values.
        held_responses = held_behavioural_responses(person, period)
        for adult_index in range(1, 1 + adult_count):
            name = f"adult_{adult_index}_pay_rise"
            while name in simulation.branches or name == simulation.branch_name:
                name += "_"
            alt_simulation = simulation.get_branch(name)
            try:
                mask = adult_index_values == adult_index
                retained = retained_input_variables(alt_simulation)
                for variable in simulation.tax_benefit_system.variables:
                    variable_data = simulation.tax_benefit_system.variables[variable]
                    if (
                        variable not in retained
                        and not variable_data.is_input_variable()
                    ):
                        alt_simulation.delete_arrays(variable)
                hold_behavioural_responses(alt_simulation, period, held_responses)
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
            finally:
                if simulation.branches.get(name) is alt_simulation:
                    del simulation.branches[name]
        return mtr_values
