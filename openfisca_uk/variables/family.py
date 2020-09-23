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


class equivalised_income(Variable):
    value_type = float
    entity = Family
    label = u"Equivalised income per week, accounting for family structure"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        second_adult = family.nb_persons(Family.ADULT) == 2
        num_young_children = family.sum(
            family.members("is_young_child", period)
        )
        num_older_children = family.sum(
            family.members("is_older_child", period)
        )
        weighting = (
            0.67
            + 0.33 * second_adult
            + 0.33 * num_older_children
            + 0.2 * num_young_children
        )
        return family("family_net_income", period) / weighting


class in_absolute_poverty(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family is in absolute poverty"
    definition_period = ETERNITY
    reference = ["https://www.ifs.org.uk/comms/comm118.pdf#page=7"]

    def formula(family, period, parameters):
        return family("equivalised_income", period) < 414


class in_relative_poverty(Variable):
    value_type = bool
    entity = Family
    label = u"Whether the family is in relative poverty"
    definition_period = ETERNITY
    reference = [
        "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/875261/households-below-average-income-1994-1995-2018-2019.pdf#page=3"
    ]

    def formula(family, period, parameters):
        return family("equivalised_income", period) < 447


class rent(Variable):
    value_type = float
    entity = Family
    label = u"Rental costs per week"
    definition_period = ETERNITY


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


class num_adults(Variable):
    value_type = int
    entity = Family
    label = u"Number of adults in the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.nb_persons(Family.ADULT)


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


class total_benefit_value(Variable):
    value_type = float
    entity = Family
    label = u"Total amount in benefits per week"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        BENEFITS = [
            "child_tax_credit",
            "working_tax_credit",
            "child_benefit",
            "income_support",
            "housing_benefit_actual",
            "contributory_JSA",
            "income_JSA",
            "DLA_SC_actual",
            "DLA_M_actual",
            "pension_credit_actual",
            "BSP_actual",
            "AFCS_actual",
            "SDA_actual",
            "AA_actual",
            "carers_allowance_actual",
            "IIDB_actual",
            "ESA_actual",
            "incapacity_benefit_actual",
            "maternity_allowance_actual",
            "guardians_allowance_actual",
            "winter_fuel_payments_actual",
        ]
        return sum(map(lambda benefit: family(benefit, period), BENEFITS))


class family_net_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):

        return (
            family("family_total_income", period)
            + family("total_benefit_value", period)
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
            - family("benefit_cap_reduction", period)
        )
