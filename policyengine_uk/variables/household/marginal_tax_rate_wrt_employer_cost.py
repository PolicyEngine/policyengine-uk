from policyengine_uk.model_api import *
from policyengine_core.variables import Variable
from policyengine_uk.utils.marginal_rates import marginal_rate_step
from policyengine_uk.utils.measurement_branches import (
    held_behavioural_responses,
    hold_behavioural_responses,
    retained_input_variables,
)


class marginal_tax_rate_wrt_employer_cost(Variable):
    label = "Marginal tax rate with respect to employer cost"
    documentation = (
        "Percent of a marginal increase in the employer's cost of employment "
        "(gross pay plus employer NI, employer pension contributions and "
        "statutory sick/maternity/paternity pay) that does not flow to "
        "household net income. Gross pay rises by "
        "gov.simulation.marginal_tax_rate_delta, or 0.1% of employment income "
        "where that is larger, so that float32 rounding stays negligible at any "
        "level of earnings."
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
        baseline_employer_cost = person("employer_cost", period)
        baseline_net = person.household("household_net_income", period)
        # The pay rise is not a reform: each branch holds the behavioural
        # responses (labour supply and realised gains) at this simulation's
        # values.
        held_responses = held_behavioural_responses(person, period)
        for adult_index in range(1, 1 + adult_count):
            name = f"adult_{adult_index}_employer_cost_mtr"
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
                new_net = alt_person.household("household_net_income", period)
                new_employer_cost = alt_person("employer_cost", period)
                net_increase = new_net - baseline_net
                employer_cost_increase = new_employer_cost - baseline_employer_cost
                safe_denominator = where(
                    employer_cost_increase != 0, employer_cost_increase, 1
                )
                mtr_values += where(mask, 1 - net_increase / safe_denominator, 0)
            finally:
                if simulation.branches.get(name) is alt_simulation:
                    del simulation.branches[name]
        return mtr_values
