from policyengine_uk.model_api import *


class housing_benefit_widowed_parents_allowance_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Widowed Parent's Allowance counted for Housing Benefit"
    documentation = (
        "The claimant's and partner's Widowed Parent's Allowance, each less "
        "£15 a week. Not modelled: the £20 weekly limit on this and the £10 "
        "war pension disregards together (HB Regs 2006 Sch 5 para 34), which "
        "cannot bind while war pensions are taken as wholly disregarded."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/7",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test
        person = benunit.members
        counted = max_(
            person("widowed_parents_allowance", period)
            - p.widowed_parents_allowance_disregard * WEEKS_IN_YEAR,
            0,
        )
        return benunit.sum(counted * person("is_claimant_or_partner", period))
