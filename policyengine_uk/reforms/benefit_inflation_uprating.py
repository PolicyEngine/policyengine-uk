from policyengine_uk.model_api import *
from typing import Union, Optional


def benefit_uprating_reform(
    rate: float,
) -> Reform:
    # Applies an increase to actual benefit amounts.
    def modify_parameters(parameters):
        dwp = parameters.gov.dwp
        uc = dwp.universal_credit
        sa = uc.standard_allowance.amount
        pc = dwp.pension_credit
        aa = dwp.attendance_allowance
        pip = dwp.pip
        dla = dwp.dla
        hmrc = parameters.gov.hmrc
        esa = dwp.ESA
        jsa = dwp.JSA
        tc = dwp.tax_credits
        wtc = tc.working_tax_credit
        ctc = tc.child_tax_credit
        benefit_parameters = [
            sa.SINGLE_YOUNG,
            sa.SINGLE_OLD,
            sa.COUPLE_YOUNG,
            sa.COUPLE_OLD,
            uc.elements.child.amount,
            uc.elements.child.first.higher_amount,
            uc.elements.child.disabled.amount,
            uc.elements.child.severely_disabled.amount,
            uc.elements.carer.amount,
            uc.elements.childcare.maximum.children["1"],
            uc.elements.childcare.maximum.children["2"],
            uc.means_test.work_allowance_with_housing,
            uc.means_test.work_allowance_without_housing,
            pc.guarantee_credit.minimum_guarantee.SINGLE,
            pc.guarantee_credit.minimum_guarantee.COUPLE,
            pc.savings_credit.threshold.SINGLE,
            pc.savings_credit.threshold.COUPLE,
            aa.higher,
            aa.lower,
            pip.daily_living.standard,
            pip.daily_living.enhanced,
            pip.mobility.standard,
            pip.mobility.enhanced,
            dla.mobility.lower,
            dla.mobility.higher,
            dla.self_care.lower,
            dla.self_care.higher,
            dla.self_care.middle,
            dwp.carers_allowance.rate,
            dwp.carer_premium.single,
            dwp.carer_premium.couple,
            dwp.sda.maximum,
            dwp.IIDB.maximum,
            hmrc.child_benefit.amount.eldest,
            hmrc.child_benefit.amount.additional,
            esa.income.amount_18_24,
            esa.income.amount_over_25,
            esa.income.couple,
            jsa.income.amount_18_24,
            jsa.income.amount_over_25,
            jsa.income.couple,
            wtc.elements.basic,
            wtc.elements.couple,
            wtc.elements.lone_parent,
            wtc.elements.worker,
            wtc.elements.disabled,
            wtc.elements.severely_disabled,
            ctc.elements.child_element,
            ctc.elements.dis_child_element,
            ctc.elements.severe_dis_child_element,
            tc.means_test.income_threshold,
            tc.means_test.income_threshold_CTC_only,
        ]
        for parameter in benefit_parameters:
            print(parameter.name)
            for parameter_at_instant in parameter.values_list:
                parameter_at_instant.value *= rate

        for parameter in parameters.get_descendants():
            if isinstance(parameter, ParameterNode):
                parameter._at_instant_cache = {}
        parameters._at_instant_cache = {}
        return parameters

    class reform(Reform):
        def apply(self):
            self.modify_parameters(modify_parameters)

    return reform


def create_benefit_inflation_uprating_reform(parameters, period):
    uprating_amount = (
        parameters.gov.contrib.benefit_uprating.inflation_adjustment(period)
    )
    if uprating_amount != 0:
        return benefit_uprating_reform(
            rate=1 + uprating_amount,
        )
