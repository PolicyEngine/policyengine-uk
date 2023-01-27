from policyengine_uk.model_api import *


class marginal_tax_rate(Variable):
    label = "Marginal tax rate"
    documentation = "Percent of marginal income gains that do not increase household net income."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(person, period, parameters):
        mtr_values = np.zeros(person.count, dtype=np.float32)
        simulation = person.simulation
        adult_index_values = person("adult_index", period)
        DELTA = 1_000
        for adult_index in [1]:
            alt_simulation = simulation.get_branch(
                f"adult_{adult_index}_pay_rise"
            )
            mask = adult_index_values == adult_index
            for variable in simulation.tax_benefit_system.variables:
                if variable not in simulation.input_variables:
                    alt_simulation.delete_arrays(variable)
            alt_simulation.set_input(
                "employment_income",
                period,
                person("employment_income", period) + mask * DELTA,
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
        return mtr_values
