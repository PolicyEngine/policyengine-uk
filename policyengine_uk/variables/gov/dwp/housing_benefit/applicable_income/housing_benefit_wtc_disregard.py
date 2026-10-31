from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
    housing_benefit_applicable_income_childcare_element,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_childcare_earnings_limit import (
    hb_childcare_earnings_limit,
    hb_wtc_disregard,
    housing_benefit_childcare_earnings_limit,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
    hb_uses_annual_override,
)


def hb_fixed_childcare_deduction(benunit, period, parameters):
    """The annual childcare deduction where it, or the limit it reads, is
    supplied (by a dataset, set_input or a scenario), neutralized or
    calculated by a formula a reform put in place of the model's. Otherwise
    None: each accommodation segment calculates its own deduction."""
    childcare = housing_benefit_applicable_income_childcare_element
    if hb_uses_annual_override(benunit, period, childcare.__name__, childcare.formula):
        return benunit(childcare.__name__, period)
    limit = housing_benefit_childcare_earnings_limit
    if hb_uses_annual_override(benunit, period, limit.__name__, limit.formula):
        return min_(
            hb_capped_childcare_charges(benunit, period, parameters),
            benunit(limit.__name__, period),
        )
    return None


def hb_segment_childcare_deduction(benunit, period, parameters, accommodation):
    """The childcare deduction in force where the accommodation disregard has
    this full annual amount: the annual deduction where
    hb_fixed_childcare_deduction gives one, and otherwise the lesser of the
    capped charge and the earnings and tax-credit limit."""
    childcare = hb_fixed_childcare_deduction(benunit, period, parameters)
    if childcare is not None:
        return childcare
    return min_(
        hb_capped_childcare_charges(benunit, period, parameters),
        hb_childcare_earnings_limit(benunit, period, parameters, accommodation),
    )


def hb_segment_wtc_disregard(benunit, period, parameters, accommodation, childcare):
    """The WTC disregard in one accommodation segment, where Sch 4 para
    17(3)(b) counts this childcare deduction. A supplied, neutralized or
    replaced annual amount applies in every segment."""
    name = "housing_benefit_wtc_disregard"
    if hb_uses_annual_override(
        benunit, period, name, housing_benefit_wtc_disregard.formula
    ):
        return benunit(name, period)
    return hb_wtc_disregard(benunit, period, parameters, accommodation, childcare)


class housing_benefit_wtc_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit Working Tax Credit disregard"
    documentation = (
        "Working Tax Credit disregarded before the childcare deduction when "
        "the additional-disregard work conditions hold but earnings cannot "
        "fund the additional earnings disregard. The amount is capped at "
        "WTC received and the statutory additional amount, using its dated "
        "history, including the temporary 2020 increase. The existing "
        "tax-credit active parameter suppresses it from fiscal year 2025. "
        "This is separate from the earnings-only disregard. Its earnings "
        "test counts the childcare deduction in force, as the earnings "
        "disregard does, so no accommodation segment gets both additional "
        "disregards. That deduction is the one a dataset, set_input or a "
        "reform supplies or replaces, or the one a supplied or replaced "
        "limit gives; otherwise it is the deduction the model calculates in "
        "the segment. Where the accommodation disregard starts within the fiscal "
        "year, each effective-date segment has its own earnings test, as "
        "the earnings disregard does; this annual amount combines the "
        "segments' disregards, and entitlement deducts each segment's own."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/56",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/40",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/58",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/6/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2020/371/regulation/5",
        "https://www.legislation.gov.uk/nisr/2020/53/regulation/5",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
    )

    def formula(benunit, period, parameters):
        return sum(
            hb_wtc_disregard(
                benunit,
                period,
                parameters,
                accommodation,
                hb_segment_childcare_deduction(
                    benunit, period, parameters, accommodation
                ),
            )
            * share
            for accommodation, share in hb_accommodation_segments(
                benunit, period, parameters
            )
        )
