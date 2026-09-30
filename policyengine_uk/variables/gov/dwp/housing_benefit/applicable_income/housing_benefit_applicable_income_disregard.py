from policyengine_uk.model_api import *


class housing_benefit_applicable_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income disregards"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2006/213/schedule/4"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        # Hours of the claimant and partner and, as the model did before, the
        # legacy children or young persons; anyone else in the benefit unit
        # does not count (Sch 4 para 17 tests the claimant's or partner's work).
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        hours = add_for_members(benunit, period, ["weekly_hours"], members)
        # The claimant categories are mutually exclusive (Sch 4 paras 4, 7, 10).
        # Worker disregard is additional.
        single = benunit("is_single_person", period)
        single_disregard = single * p.single
        couple = benunit("is_couple", period)
        couple_disregard = couple * p.couple
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_disregard = lone_parent * p.lone_parent
        hour_requirement = where(lone_parent, WTC.min_hours.lower, p.worker_hours)
        worker = hours > hour_requirement
        worker_disregard = worker * p.worker
        weekly_disregard = (
            single_disregard
            + couple_disregard
            + lone_parent_disregard
            + worker_disregard
        )
        return weekly_disregard * WEEKS_IN_YEAR
