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
        takeup_rate = parameters(period).gov.hmrc.child_benefit.takeup
        overall_p = takeup_rate.overall
        return (random(benunit) < overall_p) * ~benunit(
            "child_benefit_opts_out", period
        )


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether this family would opt out of receiving Child Benefit payments"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        if hasattr(benunit.simulation, "dataset"):
            ani = benunit.members("adjusted_net_income", period)
            hmrc = parameters(period).gov.hmrc
            cb_hitc = hmrc.income_tax.charges.CB_HITC
            cb = hmrc.child_benefit
            in_phase_out = ani > cb_hitc.phase_out_end
            return where(
                benunit.any(in_phase_out),
                random(benunit) < cb.opt_out_rate,
                False,
            )
        else:
            # If we're not in a microsimulation, assume the family would not opt out
            return False


class child_benefit_respective_amount(Variable):
    label = "Child Benefit (respective amount)"
    documentation = "The amount of this benefit unit's Child Benefit which is in respect of this person"
    entity = Person
    definition_period = MONTH
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
            eligible &= (
                person.benunit.sum(person("basic_income", period.this_year))
                == 0
            )
        is_eldest = person("is_eldest_child", period.this_year)
        child_benefit = parameters(period).gov.hmrc.child_benefit.amount
        amount = where(
            is_eldest, child_benefit.eldest, child_benefit.additional
        )
        return eligible * amount * WEEKS_IN_YEAR / MONTHS_IN_YEAR


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
