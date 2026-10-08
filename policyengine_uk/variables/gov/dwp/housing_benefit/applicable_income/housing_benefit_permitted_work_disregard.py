from policyengine_uk.model_api import *


class housing_benefit_permitted_work_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit permitted-work earnings disregard"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/10A",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        adult = person("is_claimant_or_partner", period)
        earnings = person("housing_benefit_person_net_earnings", period) * adult
        limits = person("housing_benefit_permitted_work_limit", period) * adult
        exempt = limits > 0
        amount = benunit.max(limits) * WEEKS_IN_YEAR
        contributions = benunit.sum(
            where(exempt, earnings, min_(earnings, p.special * WEEKS_IN_YEAR))
        )
        permitted = min_(amount, contributions)
        lone_parent = where(
            benunit("is_lone_parent", period),
            min_(benunit.sum(earnings), p.lone_parent * WEEKS_IN_YEAR),
            0,
        )
        return where(benunit.any(exempt), max_(permitted, lone_parent), 0)
