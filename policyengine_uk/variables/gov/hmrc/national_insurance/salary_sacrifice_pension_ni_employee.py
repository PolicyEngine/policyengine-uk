from policyengine_uk.model_api import *


def _employee_class_1(earnings, class_1):
    """Employee Class 1 contributions on a month's earnings.

    The same schedule as ni_class_1_employee_primary plus
    ni_class_1_employee_additional.
    """
    primary_threshold = (
        class_1.thresholds.primary_threshold * WEEKS_IN_YEAR / MONTHS_IN_YEAR
    )
    upper_earnings_limit = (
        class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR / MONTHS_IN_YEAR
    )
    above_upper_earnings_limit = max_(earnings - upper_earnings_limit, 0)
    main_rate_earnings = (
        max_(earnings - primary_threshold, 0) - above_upper_earnings_limit
    )
    return (
        class_1.rates.employee.main * main_rate_earnings
        + class_1.rates.employee.additional * above_upper_earnings_limit
    )


class salary_sacrifice_pension_ni_employee(Variable):
    label = "Employee NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employee Class 1 National Insurance due because salary "
        "sacrifice pension contributions above the cap return to employment "
        "income. It is the employee's complete Class 1 liability "
        "(ni_class_1_employee) on their earnings, less the liability on the "
        "same earnings without the amount returned "
        "(salary_sacrifice_returned_to_income). The amount returned is the "
        "top slice of earnings: it bears the main rate between the primary "
        "threshold and the upper earnings limit, the additional rate above "
        "the limit, and nothing below the threshold or for a person who is "
        "not liable to primary contributions (ni_liable). "
        "\n\n"
        "This measures part of ni_class_1_employee, which already charges the "
        "amount returned. Do not add it to a National Insurance total."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "ni_liable"
    reference = (
        "https://policyengine.org/uk/research/uk-salary-sacrifice-cap",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/8",
    )

    def formula(person, period, parameters):
        # ni_class_1_employee is a monthly variable, so the difference is taken
        # month by month, with each month's earnings and parameters.
        charge = 0
        for month in period.get_subperiods(MONTH):
            class_1 = parameters(month).gov.hmrc.national_insurance.class_1
            earnings = person("ni_class_1_income", month)
            returned = person("salary_sacrifice_returned_to_income", month)
            charge += _employee_class_1(earnings, class_1) - _employee_class_1(
                earnings - returned, class_1
            )
        return charge
