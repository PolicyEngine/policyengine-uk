from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class westminster_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Westminster CTR non-dependent deductions"
    documentation = (
        "Westminster's working-age scheme is based on the Council Tax "
        "Reduction Schemes (Default Scheme) (England) Regulations 2012, and "
        "its published summary sets out only the scale (Appendix A). The "
        "Default Scheme's para 30(3) makes one deduction for a couple, the "
        "higher, other than where there is an award of Universal Credit, so "
        "each member of a non-dependant couple with Universal Credit is "
        "deducted for, as in Merton's and Kingston upon Thames's texts."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.westminster.gov.uk/sites/default/files/media/documents/council-tax-support-scheme-for-2026-27.pdf",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/30",
    )

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "westminster_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=False,
        )
