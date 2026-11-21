from policyengine_uk.model_api import *


class firm_auto_enrolment_qualifying_earnings(Variable):
    value_type = float
    entity = Firm
    label = "Firm automatic enrolment qualifying earnings"
    documentation = (
        "Total of each enrolled employee's earnings between the lower and "
        "upper limits of the qualifying earnings band (Pensions Act 2008 "
        "s.13). Supply it as an input where per-employee pay is known. "
        "Otherwise the formula assumes every employee is paid the firm's "
        "average pay and is enrolled, giving the headcount times average pay "
        "less the lower limit, capped at the band width and floored at zero. "
        "It does not apply the earnings trigger or opt-outs, so it overstates "
        "for firms with many low-paid staff and understates where pay is "
        "spread around a low average."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Pensions Act 2008 s.13",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/13",
        ),
    ]

    def formula(firm, period, parameters):
        band = parameters(period).gov.dwp.auto_enrolment.qualifying_earnings
        paybill = firm("firm_paybill", period)
        employees = firm("firm_employees", period)
        has_employees = employees > 0
        average_pay = paybill / where(has_employees, employees, 1)
        per_employee = min_(
            max_(average_pay - band.lower_limit, 0),
            band.upper_limit - band.lower_limit,
        )
        return where(has_employees, employees * per_employee, 0)
