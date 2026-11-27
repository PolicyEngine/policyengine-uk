from policyengine_uk.model_api import *


class firm_class_1b_ni(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1B National Insurance"
    documentation = (
        "Class 1B contributions on the firm's PAYE settlement agreements "
        "(SSCBA 1992 s.10A): the Class 1B percentage of the chargeable "
        "earnings included in the agreements plus the income tax the firm "
        "is accountable for under them. The percentage equals the secondary "
        "Class 1 percentage, read at 30 April (s.10A(6)), except 14.53% in "
        "2022-23 (Health and Social Care Levy (Repeal) Act 2022 Schedule "
        "para 3). There is no threshold, and the Employment Allowance cannot "
        "be set against it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.10A",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/10A",
        ),
        dict(
            title="Health and Social Care Levy (Repeal) Act 2022 Schedule paragraph 3",
            href="https://www.legislation.gov.uk/ukpga/2022/43/schedule/paragraph/3/enacted",
        ),
    ]

    def formula(firm, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        fixed = ni.class_1b.percentage_2022_23
        if fixed.in_effect:
            rate = fixed.rate
        else:
            rate = ni.class_1.employer_scale.components[1].rate
        earnings = max_(firm("firm_psa_chargeable_earnings", period), 0)
        tax = max_(firm("firm_psa_income_tax", period), 0)
        return rate * (earnings + tax)
