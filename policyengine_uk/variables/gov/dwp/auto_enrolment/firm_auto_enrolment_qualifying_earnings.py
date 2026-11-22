from policyengine_uk.model_api import *


class firm_auto_enrolment_qualifying_earnings(Variable):
    value_type = float
    entity = Firm
    label = "Firm automatic enrolment qualifying earnings"
    documentation = (
        "Total of each enrolled employee's earnings between the lower and "
        "upper limits of the qualifying earnings band (Pensions Act 2008 "
        "s.13). Supply it as an input where per-employee pay is known. "
        "Otherwise the formula splits the workforce into three pay bands. "
        "Employees supplied as paid below the earnings trigger (s.3(1)(c); "
        "firm_employees_below_auto_enrolment_earnings_trigger and their "
        "paybill) are not enrolled and contribute nothing; this is how the "
        "trigger is applied, as the formula does not read the trigger itself. "
        "Employees supplied as paid above the upper limit "
        "(firm_employees_above_auto_enrolment_upper_limit and their paybill) "
        "each contribute the band width. The remaining employees are assumed "
        "paid the average of the remaining paybill, contributing the "
        "headcount times that average less the lower limit, capped at the "
        "band width and floored at zero; this is exact when each of them "
        "earns between the lower and upper limits. With no split supplied "
        "(all 0) every employee is treated as enrolled at the firm's average "
        "pay, so the trigger is not applied: it overstates for firms with "
        "many staff below the trigger and understates where pay is spread "
        "around a low average. It ignores the age conditions, opt-outs and "
        "opt-ins, and applies the band annually rather than per pay "
        "reference period."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Pensions Act 2008 s.3",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/3",
        ),
        dict(
            title="Pensions Act 2008 s.13",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/13",
        ),
    ]

    def formula(firm, period, parameters):
        band = parameters(period).gov.dwp.auto_enrolment.qualifying_earnings
        band_width = band.upper_limit - band.lower_limit
        paybill = firm("firm_paybill", period)
        employees = firm("firm_employees", period)
        employees_below_trigger = firm(
            "firm_employees_below_auto_enrolment_earnings_trigger", period
        )
        paybill_below_trigger = firm(
            "firm_paybill_below_auto_enrolment_earnings_trigger", period
        )
        employees_above_upper = firm(
            "firm_employees_above_auto_enrolment_upper_limit", period
        )
        paybill_above_upper = firm(
            "firm_paybill_above_auto_enrolment_upper_limit", period
        )
        employees_in_band = max_(
            employees - employees_below_trigger - employees_above_upper, 0
        )
        paybill_in_band = max_(paybill - paybill_below_trigger - paybill_above_upper, 0)
        has_employees = employees_in_band > 0
        average_pay = paybill_in_band / where(has_employees, employees_in_band, 1)
        per_employee = min_(max_(average_pay - band.lower_limit, 0), band_width)
        in_band = where(has_employees, employees_in_band * per_employee, 0)
        return in_band + employees_above_upper * band_width
