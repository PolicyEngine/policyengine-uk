from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class marginal_tax_rate_on_capital_gains(Variable):
    label = "capital gains marginal tax rate"
    documentation = "Percent of marginal capital gains that do not increase household net income."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(person, period, parameters):
        mtr_values = np.zeros(person.count, dtype=np.float32)
        simulation = person.simulation
        DELTA = 1_000
        adult_index_values = person("adult_index_cg", period)
        for adult_index in [1, 2]:
            alt_simulation = simulation.get_branch(
                f"adult_{adult_index}_cg_rise"
            )
            mask = adult_index_values == adult_index
            for variable in simulation.tax_benefit_system.variables:
                variable_data = simulation.tax_benefit_system.variables[
                    variable
                ]
                if (
                    variable not in simulation.input_variables
                    and not variable_data.is_input_variable()
                ):
                    alt_simulation.delete_arrays(variable)
            alt_simulation.set_input(
                "capital_gains",
                period,
                person("capital_gains", period) + mask * DELTA,
            )
            alt_person = alt_simulation.person
            household_net_income = person.household(
                "household_net_income", period
            )
            household_net_income_higher_earnings = alt_person.household(
                "household_net_income", period
            )
            increase = (
                household_net_income_higher_earnings - household_net_income
            )
            mtr_values += where(mask, 1 - increase / DELTA, 0)

            del simulation.branches[f"adult_{adult_index}_cg_rise"]
        return mtr_values
