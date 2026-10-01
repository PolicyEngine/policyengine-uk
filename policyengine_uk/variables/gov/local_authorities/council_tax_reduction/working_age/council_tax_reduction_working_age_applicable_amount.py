from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)


class council_tax_reduction_working_age_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction applicable amount"
    documentation = (
        "Annual applicable amount of a working-age applicant in Scotland or "
        "Wales. In Wales, an applicant with an award of Universal Credit uses "
        "the Universal Credit maximum amount, including the housing costs "
        "element (WSI 2013/3029 Sch 6 para 3; monthly amounts times 12/52 "
        "give the same annual total). Otherwise, and for every Scottish "
        "applicant including those on Universal Credit, it is the personal "
        "allowance, the amounts for children, and the adult disability, "
        "severe disability, enhanced disability and carer premiums at each "
        "country's own amounts. The employment and support allowance "
        "components are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/35",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/3",
    )

    def formula(benunit, period, parameters):
        wales = is_wales_scheme(benunit.household("country", period))
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        universal_credit_route = wales & has_universal_credit
        own_amount = add(
            benunit,
            period,
            [
                "council_tax_reduction_working_age_personal_allowance",
                "council_tax_reduction_working_age_child_amounts",
                "council_tax_reduction_working_age_adult_premiums",
            ],
        )
        return where(
            universal_credit_route,
            benunit("uc_maximum_amount", period),
            own_amount,
        )
