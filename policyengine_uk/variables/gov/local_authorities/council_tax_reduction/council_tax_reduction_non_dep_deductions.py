from policyengine_uk.model_api import *
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    apportioned_non_dependant_deductions,
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
        # A non-dependant of two or more jointly liable people is apportioned
        # equally between them (SI 2012/2885 Sch 1 para 8(5); WSI 2013/3029
        # Sch 1 para 3(5) and Sch 6 para 5(5); SSI 2021/249 reg 90(5); SSI
        # 2012/319 reg 48(5)); one who resides with only one of them is
        # deducted in full from that one (see
        # non_dependant_normally_resides_with).
        return apportioned_non_dependant_deductions(
            benunit, period, deductions, equally=True
        )
