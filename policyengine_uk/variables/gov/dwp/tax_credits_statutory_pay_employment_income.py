from policyengine_uk.model_api import *


class tax_credits_statutory_pay_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Statutory pay counted as tax credit employment income"
    documentation = (
        "Regulation 4(1)(g) counts statutory sick pay in full, being wholly "
        "taxable under ITEPA 2003 s.660. Regulation 4(1)(h) counts the amount "
        "by which a payment of statutory maternity, paternity, shared "
        "parental, adoption or parental bereavement pay exceeds £100 a week. "
        "It does not list statutory neonatal care pay, which started on 6 "
        "April 2025, after tax credits ended. The model holds annual amounts, "
        "so it applies the weekly test as if each payment were received at an "
        "even rate over the 52 weeks of the year. A payment received over "
        "fewer weeks has a higher weekly rate, so the law counts more of it."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="The Tax Credits (Definition and Calculation of Income) Regulations 2002 reg. 4(1)(g) and (h)",
        href="https://www.legislation.gov.uk/uksi/2002/2006/regulation/4",
    )

    def formula(person, period, parameters):
        weekly_disregard = parameters(
            period
        ).gov.dwp.tax_credits.means_test.statutory_pay_weekly_disregard
        annual_disregard = weekly_disregard * WEEKS_IN_YEAR
        sick_pay = person("statutory_sick_pay", period)
        parental_pay = [
            "statutory_maternity_pay",
            "statutory_paternity_pay",
            "statutory_shared_parental_pay",
            "statutory_adoption_pay",
            "statutory_parental_bereavement_pay",
        ]
        excess = sum(
            max_(person(payment, period) - annual_disregard, 0)
            for payment in parental_pay
        )
        return sick_pay + excess
