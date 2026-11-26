from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dfe.education_maintenance_allowance.ema_weekly_award import (
    ema_parameters,
    ema_routes,
    wales_birth_routes,
    valid_ema_date,
)


class ema_age_eligible(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA age eligible"
    documentation = (
        "Age and birth-cohort eligibility for the explicitly supplied academic "
        "assessment. Current fiscal-year age is not a substitute for the scheme "
        "cohort."
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
        birth = person("ema_date_of_birth", period)
        scottish = (
            valid_ema_date(birth)
            & (birth >= scotland.minimum_birth_date)
            & (birth <= scotland.maximum_birth_date)
        )
        northern_irish = (
            valid_ema_date(birth)
            & (birth >= ni.minimum_birth_date)
            & (birth <= ni.maximum_birth_date)
        )
        return (
            (in_wales & (ordinary | twentieth))
            | (in_scotland & scottish)
            | (in_ni & northern_irish)
        )
