from policyengine_uk.model_api import *


class firm_class_1_earnings_above_secondary_threshold(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1 earnings above the secondary threshold"
    documentation = (
        "Total of each employee's Class 1 earnings above the secondary "
        "threshold (SSCBA 1992 s.9). Supply it as an input where per-employee "
        "pay is known. Otherwise the formula assumes every employee is paid "
        "the firm's average pay, giving the paybill less the headcount times "
        "the annual secondary threshold, floored at zero. Where some staff "
        "earn below the threshold this understates the base, since their "
        "unused threshold is netted against others' pay."
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
        return max_(paybill - employees * secondary_threshold, 0)
