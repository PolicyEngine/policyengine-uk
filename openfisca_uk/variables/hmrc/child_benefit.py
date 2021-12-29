from openfisca_uk.model_api import *


class child_benefit_reported(Variable):
    label = "Child Benefit (reported amount)"
    documentation = "Reported amount received for Child Benefit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class is_imputed_to_take_up_child_benefit(Variable):
    label = "Is imputed to take up Child Benefit"
    documentation = "Based on a random number and the take-up rate"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).hmrc.child_benefit.takeup_rate
        return random(benunit) <= takeup_rate


class would_claim_child_benefit(Variable):
    label = "Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        claims_benefits = benunit("claims_all_entitled_benefits", period)
        imputed_takeup = benunit("is_imputed_to_take_up_child_benefit", period)
        return claims_benefits | imputed_takeup


class child_benefit_respective_amount(Variable):
    label = "Child Benefit (respective amount)"
    documentation = "The amount of this benefit unit's Child Benefit which is in respect of this person"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/part/IX",
        "https://www.legislation.gov.uk/uksi/2006/965/regulation/2",
    )

    def formula(person, period, parameters):
        eligible = person("is_child_or_QYP", period)
        is_eldest = person("is_eldest_child", period)
        child_benefit = parameters(period).hmrc.child_benefit.amount
        amount = where(
            is_eldest, child_benefit.eldest, child_benefit.additional
        )
        return eligible * amount * WEEKS_IN_YEAR


class child_benefit(Variable):
    label = "Child Benefit"
    documentation = "Total Child Benefit for the benefit unit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period):
        entitlement = benunit.sum(
            benunit.members("child_benefit_respective_amount", period)
        )
        return entitlement * benunit("would_claim_child_benefit", period)


class child_benefit_less_tax_charge(Variable):
    label = "Child Benefit (less tax charge)"
    documentation = (
        "Child Benefit, minus the Child Benefit High-Income Tax Charge"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period):
        benefit = benunit("child_benefit", period)
        charge = benunit.sum(benunit.members("CB_HITC", period))
        return benefit - charge
