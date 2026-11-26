from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


def ema_parameters(parameters, period):
    """Read the fixed source-cohort rules independently of the cash year."""
    anchor = parameters(
        period
    ).gov.dfe.education_maintenance_allowance.assessment_rule_anchor_date
    anchor_date = (
        f"{anchor // 10000:04d}-{(anchor // 100) % 100:02d}-{anchor % 100:02d}"
    )
    rules = parameters(anchor_date).gov
    return (
        rules.dfe.education_maintenance_allowance,
        rules.welsh_government.education_maintenance_allowance,
        rules.scottish_government.education_maintenance_allowance,
        rules.northern_ireland.dfe.education_maintenance_allowance,
    )


def ema_routes(person, period, shared):
    """Source-supported assessment and provider routes; no population imputation."""
    country = person("ema_assessment_country", period)
    supported = person("ema_academic_year", period) == shared.supported_academic_year
    return (
        supported & (country == Country.WALES),
        supported
        & (country == Country.SCOTLAND)
        & person("ema_scotland_highland_school", period),
        supported & (country == Country.NORTHERN_IRELAND),
    )


def valid_ema_date(value):
    """Validate YYYYMMDD using Gregorian calendar constants, not an imputed age."""
    year = value // 10000
    month = (value // 100) % 100
    day = value % 100
    leap = (year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0))
    days = np.select(
        [month == 2, np.isin(month, [4, 6, 9, 11])], [28 + leap, 30], default=31
    )
    return (
        (year >= 1)
        & (year <= 9999)
        & (month >= 1)
        & (month <= 12)
        & (day >= 1)
        & (day <= days)
    )


def wales_birth_routes(person, period, shared, wales):
    birth = person("ema_date_of_birth", period)
    supplied_start = person("ema_academic_year_start_date", period)
    start = where(supplied_start == 0, wales.academic_start_date, supplied_start)
    start_valid = (
        valid_ema_date(start)
        & (start // 10000 == shared.supported_academic_year)
        & (start <= wales.academic_start_date)
    )
    year = start // 10000
    month_day = start % 10000
    ordinary = (
        birth >= (year - wales.maximum_ordinary_birthday) * 10000 + month_day
    ) & (birth < (year + 1 - wales.minimum_ordinary_birthday) * 10000 + month_day)
    twentieth = (birth >= (year - wales.extended_birthday) * 10000 + month_day) & (
        birth < (year + 1 - wales.extended_birthday) * 10000 + month_day
    )
    prior = person("ema_supported_years_in_previous_three", period)
    twentieth &= (
        (prior >= wales.minimum_prior_receipt_years)
        & (prior <= wales.maximum_prior_receipt_years)
        & person("ema_institution_recommends_twentieth_year", period)
    )
    valid = valid_ema_date(birth) & start_valid
    return valid & ordinary, valid & twentieth, start


def exact_ema_allocation(person, period, name):
    """Read only a receipt allocation genuinely supplied for this exact period."""
    holder = person.get_holder(name)
    if period not in holder.get_input_periods(person.simulation.branch_name):
        return person.empty_array()
    return max_(0, person(name, period))


class ema_weekly_award(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    unit = GBP
    label = "EMA weekly award"
    documentation = (
        "Weekly award for one explicit source-supported academic assessment, separate "
        "from the actual weeks paid in a requested model year. This is a stock "
        "assessment amount; it is not divided by 12 on a monthly query."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )

    def formula(person, period, parameters):
        shared, wales, scotland, ni = ema_parameters(parameters, period)
        in_wales, in_scotland, in_ni = ema_routes(person, period, shared)
        eligible = (
            person("ema_age_eligible", period)
            & person("ema_course_eligible", period)
            & person("ema_duration_eligible", period)
            & person("ema_income_eligible", period)
            & person("ema_residency_conditions_met", period)
        )
        rate = select(
            [in_wales, in_scotland, in_ni],
            [wales.weekly_amount, scotland.weekly_amount, ni.weekly_amount],
            default=0,
        )
        return eligible * rate
