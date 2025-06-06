from policyengine_uk.model_api import *


class employer_ni_response_consumer_incidence(Variable):
    label = "price response to employer NI reform"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        emp_ni = parameters(period).gov.contrib.policyengine.employer_ni
        if emp_ni.consumer_incidence == 0 or emp_ni.employee_incidence == 1:
            # If consumer incidence is zero, or if the employee incidence is 100%, then there is no capital incidence.:
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

        consumption = (
            person.household("consumption", period)
            / person.household.nb_persons()
        )
        total_consumption = (consumption * person_weight).sum()
        share_of_total_consumption = consumption / total_consumption

        value = (
            amount_paid_by_employers
            * share_of_total_consumption
            * consumer_incidence
        )

        if total_consumption == 0:
            return 0

        return value
