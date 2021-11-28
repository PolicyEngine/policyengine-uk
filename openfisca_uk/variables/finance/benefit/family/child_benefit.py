from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit (reported amount)"
    definition_period = YEAR


class claims_child_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            aggr(benunit, period, ["child_benefit_reported"])
            + (
                random(benunit)
                <= parameters(period).benefit.child_benefit.takeup
            )
            + benunit("claims_all_entitled_benefits", period)
        )


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 141"

    def formula(benunit, period, parameters):
        num_children = aggr(benunit, period.this_year, ["is_child_or_QYP"])
        CB = parameters(period).benefit.child_benefit
        eldest_amount = (
            amount_between(num_children, 0, 1)
            * CB.amount.eldest
            * WEEKS_IN_YEAR
        )
        additional_amount = (
            amount_over(num_children, 1) * CB.amount.additional * WEEKS_IN_YEAR
        )
        return (eldest_amount + additional_amount) * benunit(
            "claims_child_benefit", period
        )


class child_benefit_less_tax_charge(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit entitlement, less the High Income Tax Charge"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("child_benefit", period) - aggr(
            benunit, period, ["CB_HITC"]
        )
