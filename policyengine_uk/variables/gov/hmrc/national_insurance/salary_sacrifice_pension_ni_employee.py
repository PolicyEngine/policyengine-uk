from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employee(Variable):
    label = "Employee NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employee Class 1 National Insurance due because salary "
        "sacrifice pension contributions above the cap enter NIC-only "
        "earnings. It is the employee's complete Class 1 liability "
        "(ni_class_1_employee) on their earnings, less the liability on the "
        "same earnings without the NIC-only excess "
        "(salary_sacrifice_pension_ni_excess). The excess is the "
        "top slice of earnings: it bears the main rate between the primary "
        "threshold and the upper earnings limit, the additional rate above "
        "the limit, and nothing below the threshold or for a person who is "
        "not liable to primary contributions (ni_liable). "
        "\n\n"
        "This measures part of ni_class_1_employee, which already charges the "
        "NIC-only excess. Do not add it to a National Insurance total."
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
            excess = person("salary_sacrifice_pension_ni_excess", month)
            scale = class_1.employee_scale
            factor = WEEKS_IN_YEAR / MONTHS_IN_YEAR
            monthly_charge = scale.calc(earnings, factor=factor) - scale.calc(
                earnings - excess, factor=factor
            )
            directors = class_1.directors.full_year_category_a_2022_23
            if directors.in_effect:
                annual_earnings = person("ni_class_1_income", period)
                annual_excess = person("salary_sacrifice_pension_ni_excess", period)
                annual_charge = directors.employee_scale.calc(
                    annual_earnings
                ) - directors.employee_scale.calc(annual_earnings - annual_excess)
                monthly_charge = where(
                    person("is_full_year_category_a_director", period),
                    annual_charge / MONTHS_IN_YEAR,
                    monthly_charge,
                )
            charge += monthly_charge
        return charge
