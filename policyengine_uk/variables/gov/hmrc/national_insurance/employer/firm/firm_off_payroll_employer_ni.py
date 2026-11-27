from policyengine_uk.model_api import *


class firm_off_payroll_employer_ni(Variable):
    value_type = float
    entity = Firm
    label = "Firm off-payroll employer National Insurance"
    documentation = (
        "Secondary Class 1 contributions the firm pays as the fee-payer on "
        "deemed direct payments under the off-payroll working rules (SI "
        "2000/727 regs 14 and 18(2)(d)): the secondary percentage on the "
        "payments above the secondary threshold for each deemed worker. The "
        "rules apply to public authority clients from 6 April 2017 and to "
        "other clients from 6 April 2021. The Employment Allowance cannot be "
        "set against these contributions (NICA 2014 ss.1(2)(b) and 2(4)), so "
        "they are kept out of firm_employer_ni_before_allowance and the "
        "prior-year limit. The payments count in the apprenticeship levy pay "
        "bill. Like the average-pay approximation, the threshold for "
        "several workers is netted across them."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions (Intermediaries) Regulations 2000 reg 14",
            href="https://www.legislation.gov.uk/uksi/2000/727/regulation/14",
        ),
        dict(
            title="Social Security Contributions (Intermediaries) Regulations 2000 reg 18",
            href="https://www.legislation.gov.uk/uksi/2000/727/regulation/18",
        ),
        dict(
            title="National Insurance Contributions Act 2014 s.2(4)",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/2",
        ),
    ]

    def formula(firm, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        secondary = class_1.employer_scale.components[1]
        threshold = secondary.threshold * WEEKS_IN_YEAR
        payments = firm("firm_off_payroll_levy_earnings", period)
        workers = max_(firm("firm_off_payroll_deemed_workers", period), 0)
        return secondary.rate * max_(payments - workers * threshold, 0)
