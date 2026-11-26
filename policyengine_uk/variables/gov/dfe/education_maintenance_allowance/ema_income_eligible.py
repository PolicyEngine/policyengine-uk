from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dfe.education_maintenance_allowance.ema_weekly_award import (
    ema_parameters,
    ema_routes,
)


class ema_income_eligible(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA income eligible"
    documentation = (
        "Financial assessment condition for the selected scheme, respecting its own "
        "assessed-income thresholds and exemption categories."
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
        category = person("ema_financial_category", period)
        known_category = category != category.possible_values.UNKNOWN
        names = category.decode_to_str()
        welsh_exempt = np.isin(names, list(wales.income_exempt_categories))
        scottish_exempt = np.isin(names, list(scotland.income_exempt_categories))
        other = person("ema_other_qualifying_dependants", period)
        income = person("ema_assessed_income", period)
        known = (
            person("ema_income_is_known", period)
            & np.isfinite(income)
            & (other >= 0)
            & known_category
        )
        welsh_limit = where(
            other >= wales.higher_band_minimum_other_dependants,
            wales.multiple_dependants_income_limit,
            wales.single_dependant_income_limit,
        )
        scottish_limit = where(
            other >= scotland.higher_band_minimum_other_dependants,
            scotland.multiple_dependants_income_limit,
            scotland.single_dependant_income_limit,
        )
        ni_limit = where(
            other >= ni.higher_band_minimum_other_dependants,
            ni.multiple_dependants_income_limit,
            ni.single_dependant_income_limit,
        )
        return (
            (
                in_wales
                & known_category
                & (welsh_exempt | (known & (income <= welsh_limit)))
            )
            | (
                in_scotland
                & known_category
                & (scottish_exempt | (known & (income <= scottish_limit)))
            )
            | (in_ni & known & (income <= ni_limit))
        )
