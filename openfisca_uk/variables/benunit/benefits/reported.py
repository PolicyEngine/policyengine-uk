from openfisca_core.model_api import *
from openfisca_uk.entities import *


class benunit_wtc_reported(Variable):
    value_type = float
    entity = BenUnit
    label = (
        u"Amount of Working Tax Credit reported for the Benefit Unit per week"
    )
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("working_tax_credit_reported", period)
        ) + benunit.sum(benunit.members("WTC_lump_sum_reported", period))


class benunit_ctc_reported(Variable):
    value_type = float
    entity = BenUnit
    label = (
        u"Amount of Child Tax Credit reported for the Benefit Unit per week"
    )
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("child_tax_credit_reported", period)
        ) + benunit.sum(benunit.members("CTC_lump_sum_reported", period))


class benunit_IS_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Income Support reported for the Benefit Unit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_support_reported", period))


class benunit_JSA_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of JSA reported for the Benefit Unit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("JSA_contrib_reported", period)
        ) + benunit.sum(benunit.members("JSA_income_reported", period))


class benunit_CB_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Child Benefit reported for the Benefit Unit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_benefit_reported", period))
