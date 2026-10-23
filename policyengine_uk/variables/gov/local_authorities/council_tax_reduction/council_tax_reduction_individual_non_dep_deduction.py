from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/10",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        local = parameters(period).gov.local_authorities
        country = person.household("country", period)
        countries = country.possible_values
        remunerative_work_hours = select(
            [country == countries.SCOTLAND, country == countries.WALES],
            [
                local.scotland.council_tax_reduction.non_dep_deduction.remunerative_work_hours,
                local.wales.council_tax_reduction.non_dep_deduction.remunerative_work_hours,
            ],
            default=local.england.council_tax_reduction.pensioners.non_dep_deduction.remunerative_work_hours,
        )
        income = person("council_tax_reduction_non_dep_gross_income", period)
        weekly_total_income = income / WEEKS_IN_YEAR
        on_income_related_benefit = (
            person("is_on_income_support", period)
            | person("is_on_income_based_jsa", period)
            | person("is_on_income_related_esa", period)
        )
        in_remunerative_work = (
            person("weekly_hours", period) >= remunerative_work_hours
        ) & ~on_income_related_benefit
        # The national provisions' paragraph (1)(b) applies outside
        # remunerative work. Retain the existing HB scale pending #2007.
        deduction = where(
            in_remunerative_work,
            p.amount.calc(weekly_total_income, right=True),
            p.amount.amounts[0],
        )
        return deduction * WEEKS_IN_YEAR
