from policyengine_uk.model_api import *


class maintenance_loan_candidate_benunit_income(Variable):
    value_type = float
    entity = Person
    label = "Maintenance loan candidate sponsor benefit-unit income"
    documentation = (
        "Benefit-unit adjusted net income for a person, used when selecting a "
        "maintenance loan sponsor proxy from household members."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person.benunit.sum(person.benunit.members("adjusted_net_income", period))
