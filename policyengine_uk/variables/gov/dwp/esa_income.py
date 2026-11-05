from policyengine_uk.model_api import *


def income_related_esa_award(benunit, period, reported_award):
    """Income-related ESA paid on a reported award: the award less tariff
    income from capital, or nothing if the benefit unit fails the screen in
    esa_income_eligible."""
    tariff_income = benunit("esa_income_tariff_income", period)
    eligible = benunit("esa_income_eligible", period)
    return where(eligible, max_(0, reported_award - tariff_income), 0)


def income_related_esa_award_on_reports(benunit, period, reported, members=None):
    """Screen open person reports, retaining each original claim's ownership.

    The claimant and partner share one claim. Other reporters have separate
    claims, each using the existing own-work and shared-capital/tariff proxy.
    Selecting members changes only reports, never the original couple or
    the work/capital screen. This helper must not read payable-person status,
    which itself depends on the aggregate award.
    """
    person = benunit.members
    rules = benunit.simulation.tax_benefit_system.parameters(period).gov.dwp.ESA
    if members is not None:
        reported = reported * members
    couple = person("is_claimant_or_partner", period)
    couple_award = income_related_esa_award(
        benunit, period, benunit.sum(reported * couple)
    )
    works = person("esa_income_claimant_remunerative_work", period)
    capital = benunit("esa_income_assessable_capital", period)
    limit = rules.income.capital.limit
    own_claim = ~couple & ~works & benunit.project(capital <= limit)
    tariff = benunit.project(benunit("esa_income_tariff_income", period))
    own_awards = where(own_claim, max_(0, reported - tariff), 0)
    return couple_award + benunit.sum(own_awards)


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = (
        "Reported income-related ESA screened through bounded capital and "
        "remunerative work tests (esa_income_eligible). Reports whose award "
        "has ended are left out (esa_income_report_closed): the owner's "
        "legacy benefits have closed, or the owner is the claimant or "
        "partner of a family that claims Universal Credit. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        reported_award = person("esa_income_reported", period) * ~person(
            "esa_income_report_closed", period
        )
        return income_related_esa_award_on_reports(benunit, period, reported_award)
