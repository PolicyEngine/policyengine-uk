from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.measurement_branches import (
    held_behavioural_responses,
    hold_behavioural_responses,
)
from policyengine_uk.utils.marginal_rates import marginal_rate_step


class marginal_tax_rate_on_capital_gains(Variable):
    label = "capital gains marginal tax rate"
    documentation = (
        "Percent of marginal capital gains paid in capital gains tax. Realised "
        "gains reach household net income only as market income and through "
        "capital_gains_tax, so this is the share of marginal gains that does "
        "not increase household net income; it leaves out the private school "
        "attendance imputation, which ranks households by an income that "
        "includes gains. The marginal gains are added to capital_gains itself, "
        "so they are shared across the person's schedules (main rates, "
        "Business Asset Disposal Relief, residential property, carried "
        "interest) in proportion to their pre-response shares: this is a "
        "share-weighted marginal rate. The marginal gains are £1,000, or 0.1% "
        "of the gains where that is larger, and the rise in tax is divided by "
        "the rise in gains as stored, so that float32 rounding stays "
        "negligible at any size of gain. Above £1m of gains the rate is "
        "therefore averaged over the larger step."
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
        # Hold every behavioural response at this simulation's values, so each
        # branch reads its schedule split, and its earnings, instead of
        # measuring the responses again at the stepped gains.
        held_responses = held_behavioural_responses(person, period)
        # The branch recalculates only what capital gains tax depends on, a
        # fraction of what household net income does.
        tax = person("capital_gains_tax", period)
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
            hold_behavioural_responses(alt_simulation, period, held_responses)
            alt_simulation.set_input("capital_gains", period, gains + mask * step)
            alt_person = alt_simulation.person
            # Float32 rounds the higher gains, so the rise actually stored can
            # differ from the step by up to half the gains' float32 spacing.
            gains_rise = alt_person("capital_gains", period) - gains
            tax_rise = alt_person("capital_gains_tax", period) - tax
            mtr_values += where(mask, tax_rise / where(mask, gains_rise, 1), 0)

            del simulation.branches[f"adult_{adult_index}_cg_rise"]
        return mtr_values
