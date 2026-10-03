from policyengine_uk.model_api import *


class uc_childcare_treated_as_in_paid_work(Variable):
    value_type = bool
    entity = Person
    label = "Treated as in paid work for the Universal Credit childcare work condition"
    documentation = (
        "Regulation 32(2)(b): a claimant receiving statutory sick pay, "
        "statutory maternity pay, statutory paternity pay, statutory adoption "
        "pay, statutory shared parental pay, statutory parental bereavement "
        "pay, statutory neonatal care pay or maternity allowance is treated as "
        "in paid work for the work condition. Regulation 32(2)(a), ceasing "
        "paid work in the current or previous assessment period, is covered "
        "only as the annual in_work proxy covers it: hours or earnings at any "
        "point in the year count as paid work."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 32(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        ),
        dict(
            title="Advice for Decision Making ch. F7, para. F7015",
            href="https://assets.publishing.service.gov.uk/media/696a076c7b7f37aa8e4022d9/adm-ch-f7.pdf",
        ),
    ]

    def formula(person, period, parameters):
        statutory_payments = [
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "statutory_paternity_pay",
            "statutory_adoption_pay",
            "statutory_shared_parental_pay",
            "statutory_parental_bereavement_pay",
            "statutory_neonatal_care_pay",
            "maternity_allowance",
        ]
        receives = [person(payment, period) > 0 for payment in statutory_payments]
        return np.logical_or.reduce(receives)
