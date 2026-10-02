from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)


class council_tax_reduction_working_age_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction capital"
    documentation = (
        "Capital tested against the council tax reduction capital limit for a "
        "working-age claim in Scotland or Wales. A Welsh applicant with "
        "Universal Credit uses the Secretary of State's Universal Credit "
        "capital figure, and a Welsh applicant on Income Support, "
        "income-based Jobseeker's Allowance or income-related Employment and "
        "Support Allowance has all capital disregarded. Otherwise, as for "
        "other council tax reduction claims in the model, household savings "
        "stand in for the claimant's and partner's capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/66",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/30",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/10/paragraph/8",
    )

    def formula(benunit, period, parameters):
        wales = is_wales_scheme(benunit.household("country", period))
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        passported = benunit("council_tax_reduction_working_age_passported", period)
        savings = benunit.household("savings", period)
        return select(
            [wales & has_universal_credit, wales & passported],
            [benunit("uc_assessable_capital", period), 0],
            savings,
        )
