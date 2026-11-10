from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class employer_ni_response_capital_incidence(Variable):
    label = "capital response to employer NI reform"
    documentation = (
        "The part of a change in employer National Insurance that falls on "
        "capital, shared by each household's shareholding and split equally "
        "among its members. The change is the simulation's own total, which "
        "a household situation cannot know for the UK, so a situation gets 0."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        emp_ni = parameters(period).gov.contrib.policyengine.employer_ni
        if emp_ni.capital_incidence == 0 or emp_ni.employee_incidence == 1:
            # If capital incidence is zero, or if the employee incidence is 100%, then there is no capital incidence.
            return 0

        if not built_from_data(person.simulation):
            # A household situation cannot know how much employers pay across
            # the UK, so it takes no share of it.
            return 0

        person_weight = person("person_weight", period)
        baseline_employer_cost = person("baseline_employer_cost", period)
        employer_cost = person("adjusted_employer_cost", period)
        change_in_employer_cost = employer_cost - baseline_employer_cost
        amount_paid_by_employers = (person_weight * change_in_employer_cost).sum()

        # Each member takes an equal part of the household's share.
        share = person.household("shareholding", period) / person.household.nb_persons()
        return amount_paid_by_employers * share * emp_ni.capital_incidence
