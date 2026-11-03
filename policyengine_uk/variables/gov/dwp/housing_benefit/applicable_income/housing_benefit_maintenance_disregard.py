from policyengine_uk.model_api import *


class housing_benefit_maintenance_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit maintenance disregard"
    documentation = (
        "The part of the claimant's and partner's spousal maintenance that "
        "Housing Benefit disregards: £15 a week where the family includes a "
        "child or young person, nothing otherwise. Payments to the claimant "
        "and partner are added together and get one disregard (HB Regs 2006 "
        "Sch 5 para 47(2); HB (SPC) Regs 2006 Sch 5 para 20(2)). Child "
        "maintenance (maintenance_income) is not counted at all, so it needs "
        "no disregard."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/47",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/20",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test
        person = benunit.members
        maintenance = benunit.sum(
            max_(0, person("spousal_maintenance_income", period))
            * person("is_claimant_or_partner", period)
        )
        has_child = benunit.any(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        return where(
            has_child,
            min_(maintenance, p.maintenance_disregard * WEEKS_IN_YEAR),
            0,
        )
