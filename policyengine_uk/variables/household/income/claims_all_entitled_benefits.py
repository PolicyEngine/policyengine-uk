from policyengine_uk.model_api import *


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit it is entitled to. True "
        "where the benefit unit reports none of the seven means-tested "
        "benefits the formula checks (Child Tax Credit, Working Tax Credit, "
        "Universal Credit, Housing Benefit, income-based JSA, Income Support "
        "and income-related ESA); False where it reports any, in which case "
        "its reported benefits are taken as the complete set. Datasets and "
        "situations can override it directly."
    )

    def formula(benunit, period, parameters):
        # Reporting under £1 across the seven benefits counts as reporting none.
        return (
            add(
                benunit,
                period,
                [
                    "child_tax_credit_reported",
                    "working_tax_credit_reported",
                    "universal_credit_reported",
                    "housing_benefit_reported",
                    "jsa_income_reported",
                    "income_support_reported",
                    "esa_income_reported",
                ],
            )
            < 1
        )
