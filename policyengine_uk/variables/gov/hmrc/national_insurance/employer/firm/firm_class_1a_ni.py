from policyengine_uk.model_api import *


class firm_class_1a_ni(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1A National Insurance"
    documentation = (
        "Class 1A contributions the firm pays on the cash equivalent of the "
        "taxable benefits in kind it provides to employees (SSCBA 1992 "
        "s.10(1)). The Class 1A percentage equals the secondary Class 1 "
        "percentage for the year (s.10(5)), read at 30 April like other "
        "annual rates, except in 2022-23, when the Health and Social Care "
        "Levy (Repeal) Act 2022 fixes it at 14.53%. It has no threshold, and "
        "the Employment Allowance cannot be set against it. It belongs in "
        "firm_tax but not in firm_only_tax, because the household side "
        "already has Class 1A (ni_class_1a, part of ni_employer)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.10",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/10",
        ),
        dict(
            title="Health and Social Care Levy (Repeal) Act 2022 Schedule paragraph 1",
            href="https://www.legislation.gov.uk/ukpga/2022/43/schedule/paragraph/1/enacted",
        ),
    ]

    def formula(firm, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        fixed = ni.class_1a.percentage_2022_23
        if fixed.in_effect:
            rate = fixed.rate
        else:
            rate = ni.class_1.employer_scale.components[1].rate
        return rate * firm("firm_class_1a_benefits", period)
