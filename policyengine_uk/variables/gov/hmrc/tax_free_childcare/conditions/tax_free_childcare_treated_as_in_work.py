from policyengine_uk.model_api import *


class tax_free_childcare_treated_as_in_work(Variable):
    value_type = bool
    entity = Person
    label = "treated as in work for tax-free childcare"
    documentation = (
        "In work, on qualifying leave, or paid a statutory payment that SI "
        "2015/448 reg 12(1) treats as qualifying paid work: statutory sick pay "
        "(a), maternity allowance (b), statutory maternity pay (c), statutory "
        "paternity pay (f), statutory adoption pay (i), statutory parental "
        "bereavement pay (o) and statutory neonatal care pay (q). Reg 12(1) "
        "does not list statutory shared parental pay; it counts absence "
        "during shared parental leave (l), which "
        "tax_free_childcare_on_shared_parental_leave records. The condition "
        "in reg 12(3), being in qualifying paid work immediately before the "
        "period, is not modelled."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
    ]

    def formula(person, period, parameters):
        statutory_temporary_absence_pay = (
            add(
                person,
                period,
                [
                    "statutory_sick_pay",
                    "maternity_allowance",
                    "statutory_maternity_pay",
                    "statutory_paternity_pay",
                    "statutory_adoption_pay",
                    "statutory_parental_bereavement_pay",
                    "statutory_neonatal_care_pay",
                ],
            )
            > 0
        )
        return (
            person("in_work", period)
            | person("tax_free_childcare_on_qualifying_leave", period)
            | person("tax_free_childcare_on_adoption_leave", period)
            | person("tax_free_childcare_on_shared_parental_leave", period)
            | statutory_temporary_absence_pay
        )
