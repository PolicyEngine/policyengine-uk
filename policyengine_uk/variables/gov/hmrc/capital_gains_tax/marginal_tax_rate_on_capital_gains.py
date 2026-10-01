from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.marginal_rates import marginal_rate_step


class marginal_tax_rate_on_capital_gains(Variable):
    label = "capital gains marginal tax rate"
    documentation = (
        "Percent of marginal capital gains that do not increase household net "
        "income. The marginal gains are added to capital_gains itself, so they "
        "are shared across the person's schedules (main rates, Business Asset "
        "Disposal Relief, residential property, carried interest) in proportion "
        "to their pre-response shares: this is a share-weighted marginal rate. "
        "The marginal gains are £1,000, or 0.1% of the gains where that is "
        "larger, and the rise in net income is divided by the rise in gains as "
        "stored, so that float32 rounding stays negligible at any size of gain. "
        "Above £1m of gains the rate is therefore averaged over the larger step."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(person, period, parameters):
        mtr_values = np.zeros(person.count, dtype=np.float32)
        simulation = person.simulation
        gains = person("capital_gains", period)
        step = marginal_rate_step(gains, minimum=1_000)
        adult_index_values = person("adult_index_cg", period)
        for adult_index in [1, 2]:
            alt_simulation = simulation.get_branch(f"adult_{adult_index}_cg_rise")
            mask = adult_index_values == adult_index
            for variable in simulation.tax_benefit_system.variables:
                variable_data = simulation.tax_benefit_system.variables[variable]
                if (
                    variable not in simulation.input_variables
                    and not variable_data.is_input_variable()
                ):
                    alt_simulation.delete_arrays(variable)
            alt_simulation.set_input("capital_gains", period, gains + mask * step)
            alt_person = alt_simulation.person
            # Float32 rounds the higher gains, so the rise actually stored can
            # differ from the step by up to half the gains' float32 spacing.
            gains_rise = alt_person("capital_gains", period) - gains
            household_net_income = person.household("household_net_income", period)
            household_net_income_higher_gains = alt_person.household(
                "household_net_income", period
            )
            increase = household_net_income_higher_gains - household_net_income
            mtr_values += where(mask, 1 - increase / where(mask, gains_rise, 1), 0)

            del simulation.branches[f"adult_{adult_index}_cg_rise"]
        return mtr_values
