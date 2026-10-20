from policyengine_uk.model_api import *


class maintenance_loan_entitled_to_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Entitled to benefits for maintenance loan assessment"
    documentation = (
        "Proxy for the Student Finance England 'students entitled to benefits' maintenance loan schedule. "
        "This uses observable parent/disability/ESA-related signals already present in the model: "
        "income-related ESA payable to the student (HB Regs 2006 reg 56(2)(a)), and, for a student "
        "who is the claimant or partner, a disability or severe disability premium in their applicable "
        "amount (reg 56(2)(c)), which a partner's disability benefit can give. The premiums are the "
        "model's disability_premium and severe_disability_premium, which do not apply the State "
        "Pension Credit age or limited capability for work conditions."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2011/1986/regulation/71",
        "https://www.legislation.gov.uk/uksi/2011/1986/regulation/61",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/56",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/13",
    )

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
        # Reg 56(2)(c): a full-time student "whose applicable amount would, but
        # for paragraph (1), include the ... disability premium or severe
        # disability premium". For a couple the disability premium turns on
        # either partner's disability benefit (Sch 3 paras 12 and 13(1)(a)), so
        # a student whose partner receives PIP qualifies though the student
        # does not. The premiums are the claimant's family's, so this applies
        # to a student who is the claimant or partner, not to a dependant or
        # another member of the benefit unit.
        premium_in_applicable_amount = person("is_claimant_or_partner", period) & (
            (person.benunit("disability_premium", period) > 0)
            | (person.benunit("severe_disability_premium", period) > 0)
        )

        return (
            has_child
            | qualifying_disability_support
            | receives_income_related_esa
            | premium_in_applicable_amount
        )
