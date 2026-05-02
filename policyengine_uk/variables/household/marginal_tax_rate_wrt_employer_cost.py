from policyengine_uk.model_api import *
from policyengine_core.variables import Variable


class marginal_tax_rate_wrt_employer_cost(Variable):
    label = "Marginal tax rate with respect to employer cost"
    documentation = (
        "Percent of a marginal increase in the employer's cost of employment "
        "(gross pay plus employer NI, employer pension contributions and "
        "statutory sick/maternity/paternity pay) that does not flow to "
        "household net income."
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
        delta = p.marginal_tax_rate_delta
        adult_count = p.marginal_tax_rate_adults
        baseline_employer_cost = person("employer_cost", period)
        baseline_net = person.household("household_net_income", period)
        for adult_index in range(1, 1 + adult_count):
            alt_simulation = simulation.get_branch(
                f"adult_{adult_index}_employer_cost_mtr"
            )
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
                person("employment_income", period) + mask * delta,
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
        return mtr_values
