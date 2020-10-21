from openfisca_core.model_api import *
from openfisca_uk.entities import *


class benunit_WTC_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Working Tax Credit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("working_tax_credit_reported", period)
        )


class benunit_CTC_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Child Tax Credit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("child_tax_credit_reported", period)
        )


class benunit_CB_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Child Benefit per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_benefit_reported", period))


class benunit_IS_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Income Support per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_support_reported", period))


class benunit_JSA_income_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Income Support per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("JSA_income_reported", period))


class benunit_housing_benefit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Housing Benefit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("housing_benefit_reported", period))


class benunit_pension_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Pension Credit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_credit_reported", period))


class benunit_universal_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reported amount of Pension Credit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("universal_credit_reported", period)
        )
