from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables

## Family


class family_weight(Variable):
    value_type = float
    entity = Family
    label = u"FRS weighting of the benefit unit"
    definition_period = ETERNITY


# Derived variables

## Family


class younger_adult_age(Variable):
    value_type = int
    entity = Family
    label = u"Minimum age of an adult in the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.min(max_(family.members("age", period), 16))


class older_adult_age(Variable):
    value_type = int
    entity = Family
    label = u"Maximum age of an adult in the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.max(max_(family.members("age", period), 16))


class family_earnings(Variable):
    value_type = float
    entity = Family
    label = u"Amount of earnings per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members("total_earnings", period))


class family_pension_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of pension income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members("pension_income", period))


class family_total_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of total income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family("family_earnings", period) + family(
            "family_pension_income", period
        )


class family_JSA_receipt(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family receives JSA"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.any(family.members("JSA_receipt", period))


class family_IS_receipt(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family receives Income Support"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.any(family.members("IS_receipt", period))


class is_lone_parent(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family structure is a lone parent"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (family.nb_persons(Family.ADULT) == 1) * (
            family.nb_persons(Family.CHILD) > 0
        )


class is_couple(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family structure is a lone parent"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.nb_persons(Family.ADULT) == 2


class is_single(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family structure is a lone parent"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (family.nb_persons(Family.ADULT) == 1) * (
            family.nb_persons(Family.CHILD) == 0
        )


class per_capita_weight(Variable):
    value_type = int
    entity = Family
    label = u"Actual family weight, adjusted for number in the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.nb_persons() * family("family_weight", period)


class num_children_actual(Variable):
    value_type = int
    entity = Family
    label = u"Actual number of children"
    definition_period = ETERNITY


class housing_benefit_actual(Variable):
    value_type = float
    entity = Family
    label = u"Actual housing benefit received per week"
    definition_period = ETERNITY


class child_tax_credit_actual(Variable):
    value_type = float
    entity = Family
    label = u"Actual housing benefit received per week"
    definition_period = ETERNITY


class working_tax_credit_actual(Variable):
    value_type = float
    entity = Family
    label = u"Actual housing benefit received per week"
    definition_period = ETERNITY


class family_post_tax_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (
            family("family_total_income", period)
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
        )


class family_net_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (
            family("family_total_income", period)
            + family("child_tax_credit", period)
            + family("working_tax_credit", period)
            + family("child_benefit", period)
            + family("income_support", period)
            + family("housing_benefit_actual", period)
            + family("contributory_JSA", period)
            + family("income_JSA", period)
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
            - family("benefit_cap_reduction", period)
        )
