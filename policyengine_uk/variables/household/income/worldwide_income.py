from policyengine_uk.model_api import *


class is_non_domiciled(Variable):
    label = "non-domiciled"
    documentation = "Whether the person is non-domiciled for tax purposes."
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        if not hasattr(person.simulation, "dataset"):
            return 0
        if person.simulation.dataset.name != "enhanced_frs":
            return 0
        total_income = person("total_income", period)
        non_dom = parameters(period).gov.simulation.non_domiciled_status
        weight = person("person_weight", period)

        thresholds = non_dom.proportion_by_income.thresholds
        shares_of_non_doms = non_dom.proportion_by_income.amounts
        probabilities = np.zeros_like(total_income)
        ADJUSTMENT_FACTOR = 1e3
        for i in range(len(thresholds)):
            lower = thresholds[i]
            upper = thresholds[i + 1] if i + 1 < len(thresholds) else np.inf
            in_range = (total_income >= lower) & (total_income < upper)
            total_population = weight[in_range].sum()
            percent_non_dom = where(
                total_population == 0,
                0,
                shares_of_non_doms[i] / total_population,
            )
            probability = 1 - (1 - percent_non_dom) ** ADJUSTMENT_FACTOR
            probabilities[in_range] = probability

        return random(person) < probabilities


class worldwide_income(Variable):
    label = "worldwide income"
    documentation = "Income not taxed due to non-domiciled status."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        ADJUSTMENT_FACTOR = 2.7  # Gets 3.2bn from abolishing non-dom status
        total_income = person("total_income", period)
        is_non_dom = person("is_non_domiciled", period)

        return where(
            is_non_dom,
            total_income * ADJUSTMENT_FACTOR,
            0,
        )
