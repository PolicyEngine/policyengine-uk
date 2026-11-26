from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dfe.education_maintenance_allowance.ema_weekly_award import (
    ema_parameters,
    ema_routes,
    wales_birth_routes,
)


class ema_duration_eligible(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA duration eligible"
    documentation = (
        "Source-defined elapsed or supported-year limits for the supplied assessment "
        "and historical facts."
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
        ordinary, twentieth, start = wales_birth_routes(person, period, shared, wales)
        leaving_year = person("ema_school_leaving_academic_year", period)
        elapsed = person("ema_academic_year", period) - leaving_year
        welsh = (
            (leaving_year > 0)
            & (elapsed >= 0)
            & (
                ((elapsed < wales.ordinary_academic_year_window) & ordinary)
                | ((elapsed < wales.extended_academic_year_window) & twentieth)
            )
        )
        previous = person("ema_prior_supported_academic_years", period)
        extended = np.isin(
            person("ema_extended_duration_category", period).decode_to_str(),
            list(scotland.extended_duration_categories),
        )
        scottish_limit = where(
            extended,
            scotland.extended_supported_years,
            scotland.ordinary_supported_years,
        )
        scottish = (previous >= 0) & (previous < scottish_limit)
        confirmations = person("ema_prior_positive_or_negative_confirmations", period)
        northern_irish = (
            (previous >= 0)
            & (previous < ni.maximum_supported_years)
            & (confirmations >= 0)
        )
        return (in_wales & welsh) | (in_scotland & scottish) | (in_ni & northern_irish)
