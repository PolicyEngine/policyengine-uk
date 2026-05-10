from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_uc_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Hertsmere Class G Universal Credit Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hertsmere.council_tax_reduction
        weekly_earnings = benunit(
            "hertsmere_council_tax_reduction_uc_weekly_earnings", period
        )
        protected = benunit("hertsmere_council_tax_reduction_protected_group", period)
        protected_rate = where(
            weekly_earnings <= 0,
            ctr.uc_banded_scheme.out_of_work_support_rate.protected,
            ctr.uc_banded_scheme.support_rate.protected.calc(weekly_earnings + 1e-9),
        )
        non_protected_rate = where(
            weekly_earnings <= 0,
            ctr.uc_banded_scheme.out_of_work_support_rate.non_protected,
            ctr.uc_banded_scheme.support_rate.non_protected.calc(
                weekly_earnings + 1e-9
            ),
        )
        return where(protected, protected_rate, non_protected_rate)
