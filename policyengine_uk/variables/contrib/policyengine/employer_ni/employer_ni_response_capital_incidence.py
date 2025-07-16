from policyengine_uk.model_api import *


class employer_ni_response_capital_incidence(Variable):
    label = "capital response to employer NI reform"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.contrib.policyengine.employer_ni
        if p.capital_incidence == 0 or p.employee_incidence == 1:
            # If capital incidence is zero, or if the employee incidence is 100%, then there is no capital incidence.:
            return 0

        if not hasattr(person.simulation, "dataset"):
            # In single-household simulations, we can't automatically put revenue into price increases because we don't know the revenue.
            return 0

        person_weight = person("person_weight", period)
        baseline_employer_cost = person("baseline_employer_cost", period)
        employer_cost = person("adjusted_employer_cost", period)
        change_in_employer_cost = employer_cost - baseline_employer_cost
        amount_paid_by_employers = (
            person_weight * change_in_employer_cost
        ).sum()

        wealth = (
            person.household("corporate_wealth", period)
            / person.household.nb_persons()
        )
        total_wealth = (wealth * person_weight).sum()
        share_of_total_wealth = wealth / total_wealth

        value = (
            amount_paid_by_employers
            * share_of_total_wealth
            * p.capital_incidence
        )

        if total_wealth == 0:
            return 0

        return value
