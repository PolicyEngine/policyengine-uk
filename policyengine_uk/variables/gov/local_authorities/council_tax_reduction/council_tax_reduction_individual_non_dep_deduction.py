from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._national_non_dependants import (
    household_head_family_is_pensioner,
    individual_non_dep_deduction,
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
        "variables. Reported under the scheme of the household head's family; "
        "each applicant's deductions use its own scheme."
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
        return individual_non_dep_deduction(
            person,
            period,
            parameters,
            household_head_family_is_pensioner(person, period),
        )
