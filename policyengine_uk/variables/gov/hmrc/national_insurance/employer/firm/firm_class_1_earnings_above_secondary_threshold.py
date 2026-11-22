from policyengine_uk.model_api import *


class firm_class_1_earnings_above_secondary_threshold(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1 earnings above the secondary threshold"
    documentation = (
        "Total of each employee's Class 1 earnings above the secondary "
        "threshold (SSCBA 1992 s.9). Supply it as an input where per-employee "
        "pay is known. Otherwise the formula removes any employees supplied "
        "as paid at or below the annual secondary threshold "
        "(firm_employees_below_secondary_threshold and "
        "firm_paybill_below_secondary_threshold), then assumes the rest are "
        "paid above the threshold: the remaining paybill less the "
        "remaining headcount times the threshold, floored at zero. This is "
        "exact when every remaining employee earns above the threshold. With "
        "no split supplied (both 0) it is the plain average-pay "
        "approximation, which understates the base where some staff earn "
        "below the threshold, since their unused threshold is netted against "
        "others' pay. The threshold is applied annually rather than per "
        "earnings period. Inconsistent inputs are clipped silently: the "
        "headcount at or below the threshold is floored at zero and capped "
        "at firm_employees, and their paybill is floored at zero and capped "
        "at the lower of firm_paybill and that headcount times the threshold."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        ),
    ]

    def formula(firm, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        secondary_threshold = (
            class_1.employer_scale.components[1].threshold * WEEKS_IN_YEAR
        )
        paybill = firm("firm_paybill", period)
        employees = firm("firm_employees", period)
        employees_below = min_(
            max_(firm("firm_employees_below_secondary_threshold", period), 0),
            employees,
        )
        paybill_below = min_(
            max_(firm("firm_paybill_below_secondary_threshold", period), 0),
            min_(paybill, employees_below * secondary_threshold),
        )
        return max_(
            (paybill - paybill_below)
            - (employees - employees_below) * secondary_threshold,
            0,
        )
