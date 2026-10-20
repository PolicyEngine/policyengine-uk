from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._national_non_dependants import (
    household_head_family_is_pensioner,
    non_dep_deduction_exempt,
)


class council_tax_reduction_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "national Council Tax Reduction makes no non-dependant deduction for this person"
    documentation = (
        "Modelled exemptions in the England pensioner, Scottish and Welsh "
        "schemes: a full-time student; a non-dependant on Income Support, "
        "income-based JSA, income-related ESA or State Pension Credit (any "
        "age), and in Scotland's working-age scheme from April 2022 one whose "
        "partner is on Income Support, income-based JSA or income-related ESA "
        "and who is not on Universal Credit; an adult for whom someone else is "
        "entitled to child benefit (LGFA 1992 Sch 1 para 3); and, from the year "
        "each scheme added it, "
        "one entitled to Universal Credit calculated on no earned income. Wales excludes "
        "members of the ESA work-related activity group; with no ESA group "
        "input, income-related ESA is treated as exempt. Not modelled: other "
        "persons disregarded for council tax discounts (LGFA 1992 Sch 1), "
        "youth training allowances, a normal home elsewhere, and "
        "absence in hospital or on armed forces operations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4",
        "https://www.legislation.gov.uk/ukpga/1992/14/schedule/1/paragraph/3",
    )

    def formula(person, period, parameters):
        # Under the scheme of the household head's family; each applicant's
        # deductions use its own scheme (council_tax_reduction_non_dep_deductions).
        return non_dep_deduction_exempt(
            person,
            period,
            parameters,
            household_head_family_is_pensioner(person, period),
        )
