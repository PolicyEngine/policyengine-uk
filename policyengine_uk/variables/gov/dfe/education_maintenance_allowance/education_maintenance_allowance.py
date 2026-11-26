from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dfe.education_maintenance_allowance.ema_weekly_award import (
    ema_parameters,
    ema_routes,
    exact_ema_allocation,
)


class education_maintenance_allowance(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    unit = GBP
    label = "Education Maintenance Allowance"
    documentation = (
        "Actual annual cash for one explicitly assessed EMA award, using lawfully "
        "allocated weeks and qualifying bonuses for the requested model year. "
        "Overlapping academic assessments are not automatically reconstructed. New "
        "cash must be disjoint from legacy adult_ema, child_ema, education_grants and "
        "other supplied income; those legacy channels are not repurposed. This is the "
        "sole new cash total, not the weekly assessment amount."
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
        weekly = person("ema_weekly_award", period)
        weeks = exact_ema_allocation(person, period, "ema_payable_weeks")
        previous = person("ema_prior_positive_or_negative_confirmations", period)
        ni_weeks = min_(weeks, max_(0, ni.maximum_confirmations - previous))
        weeks = where(in_ni, where(previous >= 0, ni_weeks, 0), weeks)
        bonuses = min_(
            exact_ema_allocation(person, period, "ema_qualifying_bonus_count"),
            ni.maximum_bonus_count,
        )
        # Confirmed bonus objectives/signatures/window and ordering are supplied
        # facts, not inferred from January/June or reconstructed from counts.
        bonus_cash = in_ni * (weekly > 0) * bonuses * ni.bonus_amount
        supported_cash = (period.start.year >= shared.first_cash_model_year) & (
            period.start.year <= shared.last_cash_model_year
        )
        birth = person("ema_date_of_birth", period)
        scottish_start = where(
            birth >= scotland.winter_entry_minimum_birth_date,
            scotland.winter_payment_start_date,
            scotland.autumn_payment_start_date,
        )
        fiscal_end = (period.start.year + 1) * 10000 + shared.fiscal_year_end_month_day
        # Fiscal2026 includes January-March2027: no calendar-year winter veto.
        start_within_cash_year = ~in_scotland | (fiscal_end >= scottish_start)
        return supported_cash * start_within_cash_year * (weekly * weeks + bonus_cash)
