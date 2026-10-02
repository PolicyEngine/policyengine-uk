from policyengine_uk.model_api import *


class maintenance_loan_entitled_to_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Entitled to benefits for maintenance loan assessment"
    documentation = (
        "Proxy for the Student Finance England 'students entitled to benefits' maintenance loan schedule. "
        "This uses observable parent/disability/ESA-related signals already present in the model; "
        "the ESA signal is income-related ESA payable to the student (HB Regs 2006 reg 56(2)(a))."
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
        # Income-related ESA payable to the student, not to a partner, parent or
        # other benefit-unit member. The schedule (SI 2011/1986 reg 71(1)(h)(iii))
        # follows the special support grant test in reg 61(2)(b), which in turn
        # follows HB Regs 2006 reg 56(2)(a): a full-time student "who is a person
        # on ... an income-related employment and support allowance", that is,
        # one to whom it "is payable" (reg 2(3A)).
        receives_income_related_esa = person("is_on_income_related_esa", period)

        return has_child | qualifying_disability_support | receives_income_related_esa
