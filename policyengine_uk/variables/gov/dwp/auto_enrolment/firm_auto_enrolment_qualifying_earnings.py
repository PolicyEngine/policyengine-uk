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
        "Employees supplied as paid at or below the earnings trigger "
        "(s.3(1)(c) requires earnings above it; "
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
        "many staff at or below the trigger and understates where pay is spread "
        "around a low average. It ignores the age conditions, opt-outs and "
        "opt-ins, and applies the band annually rather than per pay "
        "reference period. Inconsistent inputs are clipped silently: each "
        "headcount and paybill is floored at zero; the headcount at or below "
        "the trigger is capped at firm_employees and the headcount above the "
        "upper limit at the employees left; each paybill is capped at the "
        "paybill left. If the paybill above the upper limit is less than "
        "that headcount times the upper limit, the split is inconsistent and "
        "those employees and their paybill are treated as part of the "
        "remaining group instead. The paybill is "
        "firm_paybill_after_minimum_wage, firm_paybill plus any pay needed "
        "to meet the minimum wage; with a pay split supplied, that extra pay "
        "all falls in the remaining group, which overstates qualifying "
        "earnings if the low-paid staff earn at or below the earnings "
        "trigger."
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
        paybill = firm("firm_paybill_after_minimum_wage", period)
        employees = firm("firm_employees", period)
        employees_below_trigger = min_(
            max_(
                firm("firm_employees_below_auto_enrolment_earnings_trigger", period),
                0,
            ),
            employees,
        )
        paybill_below_trigger = min_(
            max_(
                firm("firm_paybill_below_auto_enrolment_earnings_trigger", period),
                0,
            ),
            paybill,
        )
        employees_above_upper = min_(
            max_(firm("firm_employees_above_auto_enrolment_upper_limit", period), 0),
            employees - employees_below_trigger,
        )
        paybill_above_upper = min_(
            max_(firm("firm_paybill_above_auto_enrolment_upper_limit", period), 0),
            paybill - paybill_below_trigger,
        )
        # Staff above the upper limit must be paid more than it in total; if
        # not, the split is inconsistent and they rejoin the remaining group.
        above_split_consistent = (
            paybill_above_upper >= employees_above_upper * band.upper_limit
        )
        employees_above_upper = where(above_split_consistent, employees_above_upper, 0)
        paybill_above_upper = where(above_split_consistent, paybill_above_upper, 0)
        employees_in_band = max_(
            employees - employees_below_trigger - employees_above_upper, 0
        )
        paybill_in_band = max_(paybill - paybill_below_trigger - paybill_above_upper, 0)
        has_employees = employees_in_band > 0
        average_pay = paybill_in_band / where(has_employees, employees_in_band, 1)
        per_employee = min_(max_(average_pay - band.lower_limit, 0), band_width)
        in_band = where(has_employees, employees_in_band * per_employee, 0)
        return in_band + employees_above_upper * band_width
