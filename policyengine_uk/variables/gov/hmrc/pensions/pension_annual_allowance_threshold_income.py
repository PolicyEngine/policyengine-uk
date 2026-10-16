from policyengine_uk.model_api import *


class pension_annual_allowance_threshold_income(Variable):
    value_type = float
    entity = Person
    label = "Threshold income for the pension annual allowance"
    documentation = (
        "FA 2004 s. 228ZA(5) threshold income. Model net_income precedes pension "
        "relief: subtracting pension_contributions_relief combines the net-pay "
        "deduction from statutory net income with the gross RAS deduction. "
        "Add back full salary sacrifice before the NICs exemption cap, except "
        "the supplied amount from "
        "arrangements before 9 July 2015. With no arrangement dates in survey "
        "data, the default treats all sacrifice as on or after that date. "
        "Exclude taxable lump-sum death benefits already included in income."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA/5"

    def formula(person, period, parameters):
        actual_sacrifice = person(
            "pension_contributions_via_salary_sacrifice_from_pay", period
        )
        grandfathered = max_(
            0, person("pension_contributions_via_salary_sacrifice_pre_2015", period)
        )
        relevant_sacrifice = max_(0, actual_sacrifice - grandfathered)
        return (
            person("net_income", period)
            - person("pension_contributions_relief", period)
            + relevant_sacrifice
            - person("pension_annual_allowance_taxable_lump_sum_death_benefits", period)
        )
