from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    council_tax_reduction_joint_liability_non_dep_deductions,
)


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
    )

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "council_tax_reduction_individual_non_dep_deduction", period
        )
        return council_tax_reduction_joint_liability_non_dep_deductions(
            benunit, period, deductions, benunit.sum(deductions)
        )
