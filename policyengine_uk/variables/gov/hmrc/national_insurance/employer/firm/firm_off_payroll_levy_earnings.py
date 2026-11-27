from policyengine_uk.model_api import *


class firm_off_payroll_levy_earnings(Variable):
    value_type = float
    entity = Firm
    label = "Firm off-payroll deemed payments within the rules"
    documentation = (
        "firm_off_payroll_deemed_payments, floored at zero, in years and for "
        "clients the off-payroll working rules cover: public authorities "
        "from 6 April 2017 and other clients from 6 April 2021. They are "
        "earnings on which the firm incurs secondary Class 1 liabilities, so "
        "they count in its apprenticeship levy pay bill (Finance Act 2016 "
        "s.100)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions (Intermediaries) Regulations 2000 reg 14",
            href="https://www.legislation.gov.uk/uksi/2000/727/regulation/14",
        ),
        dict(
            title="Finance Act 2016 s.100",
            href="https://www.legislation.gov.uk/ukpga/2016/24/section/100",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.national_insurance.class_1.off_payroll
        payments = max_(firm("firm_off_payroll_deemed_payments", period), 0)
        covered = p.in_effect & (
            firm("firm_is_public_body", period) | p.applies_to_non_public_clients
        )
        return where(covered, payments, 0)
