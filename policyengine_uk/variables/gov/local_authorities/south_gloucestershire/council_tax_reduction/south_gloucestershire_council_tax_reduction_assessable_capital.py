from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire CTR assessable capital"
    definition_period = YEAR
    unit = GBP
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"

    def formula(benunit, period, parameters):
        source_capital = benunit(
            "south_gloucestershire_council_tax_reduction_applicant_partner_capital",
            period,
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        fallback_capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        return where(source_capital >= 0, source_capital, fallback_capital)
