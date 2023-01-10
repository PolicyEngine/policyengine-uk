from policyengine_uk.model_api import *


class child_benefit_reported(Variable):
    label = "Child Benefit (reported amount)"
    documentation = "Reported amount received for Child Benefit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP


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
        already_claiming = add(benunit, period, ["child_benefit_reported"]) > 0
        takeup_rate = parameters(period).gov.hmrc.child_benefit.takeup
        baseline_cb = benunit("baseline_child_benefit_entitlement", period) > 0
        eligible = benunit("child_benefit_entitlement", period) > 0
        return select(
            [already_claiming | claims_benefits, ~baseline_cb & eligible],
            [
                True,  # Claims Child Benefit in the baseline
                random(benunit)
                < takeup_rate,  # New CB eligibility from a reform
            ],
            default=False,  # Always non-claimant
        )


class child_benefit_respective_amount(Variable):
    label = "Child Benefit (respective amount)"
    documentation = "The amount of this benefit unit's Child Benefit which is in respect of this person"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/part/IX",
        "https://www.legislation.gov.uk/uksi/2006/965/regulation/2",
    )
    defined_for = "is_child_or_QYP"

    def formula(person, period, parameters):
        eligible = True
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.withdraw_cb:
            eligible &= person("basic_income", period) == 0
        is_eldest = person("is_eldest_child", period)
        child_benefit = parameters(period).gov.hmrc.child_benefit.amount
        amount = where(
            is_eldest, child_benefit.eldest, child_benefit.additional
        )
        return eligible * amount * WEEKS_IN_YEAR


class child_benefit_entitlement(Variable):
    label = "CB entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["child_benefit_respective_amount"]


class child_benefit(Variable):
    label = "Child Benefit"
    documentation = "Total Child Benefit for the benefit unit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    category = BENEFIT
    defined_for = "would_claim_child_benefit"
    adds = ["child_benefit_entitlement"]


class child_benefit_less_tax_charge(Variable):
    label = "Child Benefit (less tax charge)"
    documentation = (
        "Child Benefit, minus the Child Benefit High-Income Tax Charge"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["child_benefit"]
    subtracts = ["CB_HITC"]


class baseline_child_benefit_entitlement(Variable):
    label = "Child Benefit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
