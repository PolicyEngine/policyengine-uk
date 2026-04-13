from policyengine_uk.model_api import *


class maintenance_loan_entitled_to_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Entitled to benefits for maintenance loan assessment"
    documentation = (
        "Proxy for the Student Finance England 'students entitled to benefits' maintenance loan schedule. "
        "This uses observable parent/disability/ESA-related signals already present in the model."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        qualifying_disability_support = (
            add(
                person,
                period,
                [
                    "pip_dl",
                    "pip_m",
                    "dla_sc",
                    "dla_m",
                    "armed_forces_independence_payment",
                ],
            )
            > 0
        )
        has_child = person("is_parent", period)
        receives_income_related_esa = person.benunit("esa_income", period) > 0

        return has_child | qualifying_disability_support | receives_income_related_esa
