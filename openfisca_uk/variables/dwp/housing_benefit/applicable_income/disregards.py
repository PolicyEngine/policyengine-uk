from openfisca_uk.model_api import *


class hb_income_disregards(Variable):
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
        weekly_disregard = (
            single_disregard
            + couple_disregard
            + lone_parent_disregard
            + worker_disregard
        )
        return weekly_disregard * WEEKS_IN_YEAR
