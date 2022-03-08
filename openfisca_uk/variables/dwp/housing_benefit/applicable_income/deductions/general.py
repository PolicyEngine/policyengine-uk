from openfisca_uk.model_api import *


class hb_general_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "HB income disregards"
    documentation = "Amount of income disregarded by means tests for Housing Benefit."
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        wtc = parameters(period).benefit.tax_credits.working_tax_credit
        means_test = parameters(period).dwp.housing_benefit.means_test
        # Calculate single, couple, lone parent, and worker disregards.
        single = benunit("is_single_person", period)
        single_disregard = single * means_test.income_disregard_single
        couple = benunit("is_couple", period)
        couple_disregard = couple * means_test.income_disregard_couple
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_disregard = (
            lone_parent * means_test.income_disregard_lone_parent
        )
        hours = add(benunit, period, ["weekly_hours"])
        hour_requirement = where(
            lone_parent, wtc.min_hours.lower, means_test.worker_hours
        )
        worker = hours > hour_requirement
        worker_disregard = worker * means_test.worker_income_disregard
        num_children = benunit.nb_persons(BenUnit.CHILD)
        childcare_amount_1 = (num_children == 1) * wtc.elements.childcare_1
        childcare_amount_2 = (num_children > 1) * wtc.elements.childcare_2
        max_weekly_childcare_amount = childcare_amount_1 + childcare_amount_2
        max_childcare_amount = max_weekly_childcare_amount * WEEKS_IN_YEAR
        childcare_element = min_(
            max_childcare_amount,
            aggr(benunit, period, ["childcare_expenses"]),
        )
        weekly_disregard = (
            single_disregard
            + couple_disregard
            + lone_parent_disregard
            + worker_disregard
            + childcare_element
        )
        return weekly_disregard * WEEKS_IN_YEAR
