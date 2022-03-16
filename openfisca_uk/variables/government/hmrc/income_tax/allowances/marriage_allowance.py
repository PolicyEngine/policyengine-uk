from openfisca_uk.model_api import *


class unused_personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Unused personal allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return max_(
            person("personal_allowance", period)
            - person("adjusted_net_income", period),
            0,
        )


class meets_marriage_allowance_income_conditions(Variable):
    label = "Meets Marriage Allowance income conditions"
    documentation = "Whether this person (and their partner) meets the conditions for this person to be eligible for the Marriage Allowance, as set out in the Income Tax Act 2007 sections 55B and 55C"
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"

    def formula(person, period):
        band = person("tax_band", period)
        bands = band.possible_values
        return (band != bands.HIGHER) & (band != bands.ADDITIONAL)


class partners_unused_personal_allowance(Variable):
    label = "Partner's unused personal allowance"
    documentation = "The personal tax allowance not used by this person's partner, if they exist"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(person, period, parameters):
        is_adult = person("is_adult", period)
        pa = person("unused_personal_allowance", period)
        return person.benunit.sum(is_adult * pa) - pa


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
    unit = "currency-GBP"

    def formula(person, period, parameters):
        marital = person("marital_status", period)
        married = marital == marital.possible_values.MARRIED
        eligible = married & person(
            "meets_marriage_allowance_income_conditions", period
        )
        transferable_amount = person(
            "partners_unused_personal_allowance", period
        )
        allowances = parameters(period).tax.income_tax.allowances
        capped_percentage = allowances.marriage_allowance.max
        max_amount = allowances.personal_allowance.amount * capped_percentage
        return eligible * min_(transferable_amount, max_amount)
