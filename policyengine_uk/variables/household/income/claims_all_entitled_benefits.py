from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit it is entitled to. In "
        "hand-entered situations it is true where the benefit unit reports "
        "under £1 in total across the seven means-tested benefits the formula "
        "checks (Child Tax Credit, Working Tax Credit, Universal Credit, "
        "Housing Benefit, income-based JSA, Income Support and income-related "
        "ESA), and false where it reports £1 or more, in which case its "
        "reported benefits are taken as the complete set. Council Tax "
        "Reduction, Pension Credit and Child Benefit are not among these "
        "seven: reporting only Pension Credit still leaves this flag true. In "
        "data-built simulations it is false for every family, so take-up of "
        "the benefits that read it follows reported claims. Datasets and "
        "situations can override it directly, except that Council Tax "
        "Reduction and Housing Benefit ignore it on data-built simulations."
    )

    def formula(benunit, period, parameters):
        # Survey runs keep main's result: no family is assumed to claim a
        # benefit it does not report, so would_claim_CTC, _WTC and _IS follow
        # reported claims (CTR and HB are reporters-only there anyway, d1390
        # and d1455). Main got there through a sum over the whole simulation,
        # which any reporting family made false for every family. Tested per
        # family instead, every non-reporting survey family would turn true
        # and claim tax credits and Income Support (PR 1831 review r6).
        if built_from_data(benunit.simulation):
            return benunit.filled_array(False)
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
