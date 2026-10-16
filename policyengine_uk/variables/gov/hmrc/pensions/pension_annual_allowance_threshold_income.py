from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import pension_contributions_relief_amount


class pension_annual_allowance_threshold_income(Variable):
    value_type = float
    entity = Person
    label = "Threshold income for the pension annual allowance"
    documentation = (
        "FA 2004 s. 228ZA(5) threshold income. Remove the NICs-only returned "
        "salary sacrifice from model income and recompute pension relief on "
        "actual member contributions and relevant earnings. This combines "
        "the net-pay deduction from statutory net income with gross RAS "
        "relief, including the basic amount and age limit. Add back full "
        "salary sacrifice before the NICs cap, except the supplied amount "
        "from arrangements before 9 July 2015. With no arrangement dates in "
        "survey data, all sacrifice defaults to on or after that date. "
        "Exclude taxable lump-sum death benefits already included in income."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA/5"

    def formula(person, period, parameters):
        returned = person("salary_sacrifice_returned_to_income", period)
        actual_sacrifice = person(
            "pension_contributions_via_salary_sacrifice_from_pay", period
        )
        grandfathered = max_(
            0, person("pension_contributions_via_salary_sacrifice_pre_2015", period)
        )
        relevant_sacrifice = max_(0, actual_sacrifice - grandfathered)
        # NICs reclassification changes neither income-tax earnings nor the
        # actual member contributions. Its relief need not equal the returned
        # amount: after 75 there is none, and low earnings can use basic RAS.
        actual_member_contributions = person("pension_contributions", period) - returned
        actual_earnings = (
            person("employment_income", period)
            - returned
            + max_(0, person("self_employment_income", period))
        )
        relief = where(
            returned > 0,
            pension_contributions_relief_amount(
                actual_member_contributions,
                actual_earnings,
                person("personal_pension_contributions", period),
                person("age", period),
                parameters(period).gov.hmrc,
            ),
            person("pension_contributions_relief", period),
        )
        return (
            person("net_income", period)
            - returned
            - relief
            + relevant_sacrifice
            - person("pension_annual_allowance_taxable_lump_sum_death_benefits", period)
        )
