from policyengine_uk.model_api import *


def income_related_jsa_award(benunit, period, reported_award):
    """Income-based JSA paid on a reported award: the award less tariff
    income from capital, or nothing if the scheme is not active or the
    benefit unit fails the screen in jsa_income_eligible."""
    JSA = benunit.simulation.tax_benefit_system.parameters(period).gov.dwp.JSA
    if not JSA.income.active:
        return benunit.empty_array()
    tariff_income = benunit("jsa_income_tariff_income", period)
    eligible = benunit("jsa_income_eligible", period)
    return where(eligible, max_(0, reported_award - tariff_income), 0)


def income_related_jsa_award_on_reports(benunit, period, reported, members=None):
    """Screen open person reports, retaining each original claim's ownership.

    The claimant and partner share one claim. Other reporters have separate
    claims, each using the existing own-work and shared-capital/tariff proxy.
    Selecting members changes only reports, never the original couple or
    the work/capital screen. This helper must not read payable-person status,
    which itself depends on the aggregate award.
    """
    person = benunit.members
    rules = benunit.simulation.tax_benefit_system.parameters(period).gov.dwp.JSA
    if not rules.income.active:
        return benunit.empty_array()
    if members is not None:
        reported = reported * members
    couple = person("is_claimant_or_partner", period)
    couple_award = income_related_jsa_award(
        benunit, period, benunit.sum(reported * couple)
    )
    works = (
        person("jsa_remunerative_work_hours", period)
        >= rules.remunerative_work.claimant_hours
    )
    capital = benunit("jsa_income_assessable_capital", period)
    limit = rules.income.capital.limit
    own_claim = ~couple & ~works & benunit.project(capital <= limit)
    tariff = benunit.project(benunit("jsa_income_tariff_income", period))
    own_awards = where(own_claim, max_(0, reported - tariff), 0)
    return couple_award + benunit.sum(own_awards)


class jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    documentation = (
        "Reported income-based JSA screened through bounded capital and "
        "remunerative work tests (jsa_income_eligible). "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.JSA.income.active:
            return benunit.empty_array()
        person = benunit.members
        reported_award = person("jsa_income_reported", period) * ~person(
            "person_legacy_benefits_closed", period
        )
        return income_related_jsa_award_on_reports(benunit, period, reported_award)
