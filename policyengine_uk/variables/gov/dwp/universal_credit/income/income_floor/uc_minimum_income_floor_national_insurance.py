from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable


class uc_minimum_income_floor_national_insurance(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor deduction for National Insurance"
    documentation = (
        "The amount for National Insurance deducted from the person's gross "
        "individual threshold to give their net minimum income floor. The "
        "regulations leave it to the Secretary of State. The model takes the "
        "contributions the person would pay if the threshold were their only "
        "earnings: Class 2 and Class 4 on self-employed profits of that "
        "amount, as in DWP's figures, or primary Class 1 on pay of that "
        "amount where the parameter selects it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 62(4)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 ss. 8, 11 and 15",
            href="https://www.legislation.gov.uk/ukpga/1992/4/part/I",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period)
        ni = p.gov.hmrc.national_insurance
        threshold = person("uc_minimum_income_floor_gross", period)
        # Primary Class 1 on pay equal to the threshold, with the annual
        # thresholds (weekly amounts times 52) the model uses for employees.
        class_1 = ni.class_1
        primary_threshold = class_1.thresholds.primary_threshold * WEEKS_IN_YEAR
        upper_earnings_limit = class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR
        employee = class_1.rates.employee.main * max_(
            0, min_(threshold, upper_earnings_limit) - primary_threshold
        ) + class_1.rates.employee.additional * max_(
            0, threshold - upper_earnings_limit
        )
        # Class 2 and Class 4 on profits equal to the threshold, by the same
        # s.11(2) test and contribution weeks as ni_class_2: from 2022-23
        # profits up to the lower profits threshold are treated as paid.
        class_2 = (
            class_2_liable(threshold, ni.class_2)
            * ni.class_2.flat_rate
            * class_2_contribution_weeks(period.start.year)
        )
        class_4 = ni.class_4
        class_4_amount = class_4.rates.main * max_(
            0,
            min_(threshold, class_4.thresholds.upper_profits_limit)
            - class_4.thresholds.lower_profits_limit,
        ) + class_4.rates.additional * max_(
            0, threshold - class_4.thresholds.upper_profits_limit
        )
        # Each class is due only from those the model treats as liable for
        # it, as for the person's actual contributions. Primary Class 1 and
        # Class 2 stop at State Pension age (ni_liable). Class 4 is due for
        # the whole tax year from anyone not over it on 6 April (SI 2001/1004
        # reg. 91(a), ni_class_4_liable). No class is due from anyone under 16.
        liable = person("ni_liable", period)
        class_4_liable = person("ni_class_4_liable", period)
        self_employed = liable * class_2 + class_4_liable * class_4_amount
        mif = p.gov.dwp.universal_credit.means_test.minimum_income_floor
        return where(
            mif.self_employed_national_insurance, self_employed, liable * employee
        )
