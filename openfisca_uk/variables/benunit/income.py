from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables


class external_child_maintenance(Variable):
    value_type = float
    entity = BenUnit
    label = "Reported weeklyised amount of maintenance paid to dependent children living away from home"
    definition_period = ETERNITY


# Derived variables


class benunit_benefit_modelling(Variable):
    value_type = float
    entity = BenUnit
    label = "Difference between reported benefits and simulated benefits"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        ADDED_BENEFITS = [
            "working_tax_credit",
            "child_tax_credit",
            "child_benefit",
            "income_support",
            "JSA_income",
            "pension_credit",
            "housing_benefit",
            "universal_credit",
            "ESA_income",
        ]
        REMOVED_BENEFITS = [
            "working_tax_credit_reported",
            "WTC_lump_sum_reported",
            "child_tax_credit_reported",
            "CTC_lump_sum_reported",
            "JSA_income_reported",
            "child_benefit_reported",
            "income_support_reported",
            "SFL_IS_reported",
            "SFL_JSA_reported",
            "DWP_IS_reported",
            "DWP_JSA_reported",
            "universal_credit_reported",
            "DWP_UC_reported",
            "SFL_UC_reported",
            "housing_benefit_reported",
            "pension_credit_reported",
            "ESA_income_reported",
        ]
        added_sum = sum(
            map(lambda benefit: benunit(benefit, period), ADDED_BENEFITS)
        )
        removed_sum = sum(
            map(
                lambda benefit: benunit.sum(benunit.members(benefit, period)),
                REMOVED_BENEFITS,
            )
        )
        return added_sum - removed_sum


class benunit_taxed_means_tested_bonus(Variable):
    value_type = float
    entity = BenUnit
    label = u"Total untaxed means tested bonus"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("taxed_means_tested_bonus", period))


class benunit_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income of the benefit unit (not including benefits)"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income", period))


class benunit_interest(Variable):
    value_type = float
    entity = BenUnit
    label = u"Interest received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("interest", period))


class benunit_misc(Variable):
    value_type = float
    entity = BenUnit
    label = u"Miscellaneous income per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("misc_income", period))


class benunit_pension_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_income", period))


class benunit_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension and earnings for the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("pension_income", period)
            + benunit.members("earnings", period)
            + benunit.members("interest", period)
        )


class benunit_state_pension(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("state_pension", period))


class benunit_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Earnings of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("earnings", period))


class benunit_post_tax_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Post-tax income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("post_tax_income", period))


class benunit_gross_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Gross income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("gross_income", period))


class benunit_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Tax paid by the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_tax", period))


class benunit_NI(Variable):
    value_type = float
    entity = BenUnit
    label = u"National Insurance paid by the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("NI", period))


class benunit_net_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Net income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("net_income", period))


class equiv_benunit_net_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Equivalised net income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("benunit_net_income", period) / benunit(
            "benunit_equivalisation", period
        )


class benunit_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Income Tax per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_tax", period))


class benunit_NI(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of National Insurance per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("NI", period))


class benunit_receiving_unemployment_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit receives JSA"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (benunit("JSA_income", period) > 0) + (
            benunit.sum(benunit.members("JSA_contrib", period)) > 0
        ) > 0


class benunit_receiving_disability_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit receives disability benefits"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit.sum(benunit.members("total_disability_benefits", period))
            > 0
        )


class benunit_receiving_income_support(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit receives IS"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit.sum(benunit.members("income_support_reported", period)) > 0
        )


class benunit_receiving_tax_credits(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the person receives the Tax Credits"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit.sum(benunit.members("working_tax_credit_reported", period))
            + benunit.sum(benunit.members("child_tax_credit_reported", period))
            > 0
        )


class couple_childless_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether a benefit unit with two adults and no children"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_couple", period) * (
            benunit.nb_persons(BenUnit.CHILD) == 0
        )


class couple_parents_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether a benefit unit with two adults and dependent children"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_couple", period) * (
            benunit.nb_persons(BenUnit.CHILD) > 0
        )


class self_emp_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether a benefit unit with a self-employed person"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit.sum(benunit.members("self_employed_earnings", period)) > 0
        )


class capital_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether a benefit unit with all income from capital"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit.sum(benunit.members("interest", period))
            + benunit.sum(benunit.members("pension_income", period))
            > 0
        ) * (benunit.sum(benunit.members("earnings", period)) == 0)


class benunit_in_poverty_bhc(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benefit unit is in a household in BHC poverty"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("person_in_poverty_bhc", period))
