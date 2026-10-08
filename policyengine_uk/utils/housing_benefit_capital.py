"""Category-specific Housing Benefit capital exclusions, using retained stocks."""

import numpy as np

from policyengine_uk.utils.housing_benefit import calendar_dates


_UNKNOWN = np.datetime64("9999-01-01")


def year_after(dates):
    """One calendar year, retaining the day or the final day of February."""
    month = dates.astype("datetime64[M]")
    day = (dates - month.astype("datetime64[D]")).astype(int)
    next_month = month + np.timedelta64(12, "M")
    return np.minimum(
        next_month.astype("datetime64[D]") + day.astype("timedelta64[D]"),
        (next_month + np.timedelta64(1, "M")).astype("datetime64[D]")
        - np.timedelta64(1, "D"),
    )


def within_days(now, start, days, extension=None):
    """A statutory period beginning on receipt; extensions require a known date."""
    normal = now < start + np.timedelta64(int(days), "D")
    longer = False if extension is None else (extension < _UNKNOWN) & (now <= extension)
    return (now >= start) & (normal | longer)


def disregarded_capital(person, period, parameters, pension):
    """Keep working-age and pension-age exclusions separate for shared stocks."""
    p = parameters(period).gov.dwp.housing_benefit.means_test.capital.disregards
    now = person.benunit("housing_benefit_assessment_date", period)

    def amount(name):
        return np.maximum(person("housing_benefit_capital_" + name, period), 0)

    def fact(name):
        return person("housing_benefit_capital_" + name, period)

    start = person.benunit("housing_benefit_continuous_award_start", period)
    end = person.benunit("housing_benefit_continuous_award_end", period)
    ordinary_days = p.temporary_weeks * 7
    commencement = calendar_dates(p.carer_reassessment_commencement)
    refund = (
        amount("carer_reassessment_retained")
        * fact("carer_reassessment_provenance")
        * (now >= commencement)
        * (fact("carer_reassessment_received") <= now)
    )
    injury_date = fact("injury_first_payment_received")
    injury_active = (
        (now >= injury_date)
        if pension
        else (
            fact("injury_payment_is_first")
            & within_days(now, injury_date, p.injury_weeks * 7)
        )
    )
    injury = amount("injury_trust") + amount("injury_payment_retained") * injury_active
    arrears_date = fact("arrears_received")
    ordinary_arrears = (
        (now >= arrears_date) & (now < year_after(arrears_date))
        if pension
        else within_days(now, arrears_date, p.arrears_weeks * 7)
    )
    continuous = (arrears_date >= start) & (now >= arrears_date) & (now <= end)
    if not pension:
        continuous &= arrears_date >= calendar_dates(
            p.large_error_payment_earliest_receipt
        )
    large_error = (
        continuous
        & fact("arrears_official_error")
        & (amount("arrears_total_payment") >= p.large_error_payment)
    )
    arrears = amount("qualifying_arrears_retained") * (ordinary_arrears | large_error)
    esa_date = fact("esa_error_received")
    esa_ordinary = (
        (now >= esa_date) & (now < year_after(esa_date))
        if pension
        else within_days(now, esa_date, p.arrears_weeks * 7)
    )
    esa_large = (
        (amount("esa_error_total_payment") >= p.large_error_payment)
        & (esa_date >= start)
        & (now >= esa_date)
        & (now <= end)
    )
    arrears += amount("esa_official_error_retained") * (esa_ordinary | esa_large)
    earmarked = 0
    for category in ("home", "repairs"):
        received = fact(category + "_funds_received")
        active = (
            (now >= received) & (now < year_after(received))
            if pension
            else within_days(
                now, received, ordinary_days, fact(category + "_funds_extension_end")
            )
        )
        earmarked += amount(category + "_funds_retained") * active
    business_extension = fact("business_extension_end")
    disposal = (
        fact("business_disposal_steps")
        & (fact("business_ceased") <= now)
        & (business_extension < _UNKNOWN)
        & (now <= business_extension)
    )
    illness = fact("business_illness_and_return") & within_days(
        now, start, ordinary_days, business_extension
    )
    business = amount("business_assets") * (
        fact("business_active") | disposal | illness
    )
    category = fact("premises_category")
    types = category.possible_values
    intended = fact("premises_intended_home")
    steps = fact("premises_reasonable_steps")
    ordinary_premises = (
        ((category == types.ACQUIRED_HOME) & intended)
        | ((category == types.SALE) & steps)
        | (
            (
                (category == types.LEGAL_POSSESSION)
                | (category == types.ESSENTIAL_REPAIRS)
            )
            & intended
            & steps
        )
    )
    temporary = ordinary_premises & within_days(
        now, fact("premises_first_step"), ordinary_days, fact("premises_extension_end")
    )
    estranged = category == types.FORMER_HOME_ESTRANGEMENT
    former_lone = fact("property_occupier_is_former_partner") & fact(
        "property_occupier_is_lone_parent"
    )
    temporary |= estranged & (
        within_days(now, fact("premises_first_step"), ordinary_days) | former_lone
    )
    premises = amount("temporary_premises") * temporary
    relative = fact("property_occupier_is_relative") & (
        fact("property_occupier_over_qualifying_age")
        | fact("property_occupier_incapacitated")
    )
    former = fact("property_occupier_is_former_partner") & ~fact(
        "property_relationship_estranged"
    )
    relatives = amount("relative_occupied_premises") * (relative | former)
    return refund + injury + arrears + earmarked + business + premises + relatives
