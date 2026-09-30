from policyengine_uk.model_api import *


class uc_minimum_income_floor_national_insurance(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor deduction for National Insurance"
    documentation = (
        "The amount for National Insurance deducted from the person's gross "
        "individual threshold to give their net minimum income floor. The "
        "regulations leave it to the Secretary of State. The model takes the "
        "contributions the person would pay if the threshold were their only "
        "earnings: primary Class 1 on pay of that amount, or, where the "
        "parameter selects self-employed contributions, Class 2 and Class 4 "
        "on profits of that amount."
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
        # Class 2 and Class 4 on profits equal to the threshold.
        class_2 = (
            (threshold >= ni.class_2.small_profits_threshold)
            * ni.class_2.flat_rate
            * WEEKS_IN_YEAR
        )
        class_4 = ni.class_4
        class_4_amount = class_4.rates.main * max_(
            0,
            min_(threshold, class_4.thresholds.upper_profits_limit)
            - class_4.thresholds.lower_profits_limit,
        ) + class_4.rates.additional * max_(
            0, threshold - class_4.thresholds.upper_profits_limit
        )
        self_employed = class_2 + class_4_amount
        mif = p.gov.dwp.universal_credit.means_test.minimum_income_floor
        amount = where(mif.self_employed_national_insurance, self_employed, employee)
        # No primary Class 1, Class 2 or Class 4 is due from anyone the model
        # treats as not liable (under 16 or over State Pension age).
        return person("ni_liable", period) * amount
