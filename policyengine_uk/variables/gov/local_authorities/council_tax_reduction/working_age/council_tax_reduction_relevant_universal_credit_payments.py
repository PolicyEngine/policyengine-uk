from policyengine_uk.model_api import *


class council_tax_reduction_relevant_universal_credit_payments(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant Universal Credit payments for Scottish council tax reduction"
    documentation = (
        "The part of a Universal Credit award that Scotland's working-age "
        "council tax reduction scheme counts as income: the child element, "
        "including the disabled child additions, plus the childcare costs "
        "element, or the whole award if lower. An award with no child element "
        "counts nothing. The standard allowance and the housing, carer and "
        "limited capability elements are never income."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ssi/2021/249/regulation/57"

    def formula(benunit, period, parameters):
        child_element = benunit("uc_child_element", period)
        disabled_child_additions = add(
            benunit,
            period,
            [
                "uc_individual_disabled_child_element",
                "uc_individual_severely_disabled_child_element",
            ],
        )
        childcare_element = benunit("uc_childcare_element", period)
        award = benunit(
            "council_tax_reduction_working_age_universal_credit_award", period
        )
        has_child_element = child_element > 0
        counted = min_(
            child_element + disabled_child_additions + childcare_element, award
        )
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        return where(has_universal_credit & has_child_element, counted, 0)
