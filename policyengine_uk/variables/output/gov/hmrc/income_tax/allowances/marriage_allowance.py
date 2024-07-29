from policyengine_uk.model_api import *
from numpy import ceil


class unused_personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Unused personal allowance"
    definition_period = YEAR
    unit = GBP

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
        return (
            (band == bands.BASIC)
            | (band == bands.STARTER)
            | (band == bands.INTERMEDIATE)
        )


class partners_unused_personal_allowance(Variable):
    label = "Partner's unused personal allowance"
    documentation = "The personal tax allowance not used by this person's partner, if they exist"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        is_adult = person("is_adult", period)
        pa = person("unused_personal_allowance", period)
        return person.benunit.sum(is_adult * pa) - pa


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
    unit = GBP

    def formula(person, period, parameters):
        marital = person("marital_status", period)
        married = marital == marital.possible_values.MARRIED
        eligible = married & person(
            "meets_marriage_allowance_income_conditions", period
        )
        transferable_amount = person(
            "partners_unused_personal_allowance", period
        )
        allowances = parameters(period).gov.hmrc.income_tax.allowances
        takeup_rate = allowances.marriage_allowance.takeup_rate
        capped_percentage = allowances.marriage_allowance.max
        max_amount = allowances.personal_allowance.amount * capped_percentage
        amount_if_eligible_pre_rounding = min_(transferable_amount, max_amount)
        # Round up.
        rounding_increment = allowances.marriage_allowance.rounding_increment
        amount_if_eligible = (
            ceil(amount_if_eligible_pre_rounding / rounding_increment)
            * rounding_increment
        )
        return eligible * amount_if_eligible * (random(person) < takeup_rate)
