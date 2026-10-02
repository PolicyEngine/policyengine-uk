from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    non_dependant_weekly_gross_income,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_scotland_scheme,
    is_wales_scheme,
)


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    documentation = (
        "The England pensioner, Scottish and Welsh schemes' own weekly scales. "
        "A non-dependant in remunerative work pays the deduction for the band "
        "containing their normal gross weekly income (a couple's joint income "
        "for a claimant or partner of the non-dependant's family); bands "
        "include their lower edge. A non-dependant not in "
        "remunerative work pays the lowest amount; an exempt non-dependant "
        "pays nothing. English working-age local schemes have their own "
        "variables."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
    )

    def formula(person, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        england = (
            local_authorities.england.council_tax_reduction.pensioners.non_dep_deduction
        )
        scotland = local_authorities.scotland.council_tax_reduction.non_dep_deduction
        wales = local_authorities.wales.council_tax_reduction.non_dep_deduction
        country = person.household("country", period)
        has_pensioner = person.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        schemes = [
            is_england_pensioner_scheme(country, has_pensioner),
            is_scotland_scheme(country),
            is_wales_scheme(country),
        ]
        weekly_income = non_dependant_weekly_gross_income(person, period)
        no_income = np.zeros_like(weekly_income)
        remunerative_work_hours = select(
            schemes,
            [
                england.remunerative_work_hours,
                scotland.remunerative_work_hours,
                wales.remunerative_work_hours,
            ],
            default=np.inf,
        )
        in_remunerative_work = person("weekly_hours", period) >= remunerative_work_hours
        banded = select(
            schemes,
            [
                england.amount.calc(weekly_income),
                scotland.amount.calc(weekly_income),
                wales.amount.calc(weekly_income),
            ],
            default=0,
        )
        not_in_remunerative_work = select(
            schemes,
            [
                england.amount.calc(no_income),
                scotland.amount.calc(no_income),
                wales.amount.calc(no_income),
            ],
            default=0,
        )
        weekly = where(in_remunerative_work, banded, not_in_remunerative_work)
        # The local schemes share the eligibility variable and apply their own
        # exemptions, so the national ones apply here.
        exempt = person("council_tax_reduction_non_dep_deduction_exempt", period)
        return where(exempt, 0, weekly * WEEKS_IN_YEAR)
