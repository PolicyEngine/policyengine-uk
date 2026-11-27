from policyengine_uk.model_api import *


class firm_termination_award_class_1a_ni(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1A National Insurance on termination awards"
    documentation = (
        "Class 1A contributions on the part of each employee's termination "
        "awards above the £30,000 threshold that counts as employment "
        "income under ITEPA 2003 s.403 (SSCBA 1992 s.10(1A)-(1C)), from 6 "
        "April 2020. The Class 1A percentage equals the secondary Class 1 "
        "percentage, read at 30 April, so 2022-23 uses 15.05%: the fixed "
        "14.53% for that year does not apply to termination awards (Health "
        "and Social Care Levy (Repeal) Act 2022 Schedule paras 1(1) and "
        "2(2)), and awards paid from 6 November 2022 at 13.8% are not "
        "separated. The Employment Allowance cannot be set against it. With "
        "several recipients the threshold is netted across them."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.10",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/10",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s.403",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/403",
        ),
        dict(
            title="Health and Social Care Levy (Repeal) Act 2022 Schedule",
            href="https://www.legislation.gov.uk/ukpga/2022/43/schedule/enacted",
        ),
    ]

    def formula(firm, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        p = ni.class_1a.termination_awards
        if not p.in_effect:
            return np.zeros(firm.count)
        rate = ni.class_1.employer_scale.components[1].rate
        awards = max_(firm("firm_termination_awards", period), 0)
        recipients = max_(firm("firm_termination_award_recipients", period), 0)
        return rate * max_(awards - recipients * p.threshold, 0)
