from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)


class council_tax_reduction_devolved_working_age(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims under the Scottish or Welsh working-age council tax reduction rules"
    documentation = (
        "Whether the family lives in Scotland or Wales and is not a pensioner "
        "for council tax reduction. Scotland's working-age scheme and the "
        "Welsh rules for persons who are not pensioners have their own "
        "applicable amounts, income rules and Universal Credit route."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
    )

    def formula(benunit, period, parameters):
        country = benunit.household("country", period)
        devolved = is_scotland_scheme(country) | is_wales_scheme(country)
        pensioner = benunit("council_tax_reduction_pensioner", period)
        return devolved & ~pensioner
