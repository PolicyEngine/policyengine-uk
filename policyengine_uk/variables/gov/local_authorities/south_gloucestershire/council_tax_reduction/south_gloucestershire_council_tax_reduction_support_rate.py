from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire Council Tax Reduction support rate"
    definition_period = YEAR
    reference = [
        "https://beta.southglos.gov.uk/apply-for-council-tax-reduction/",
        "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf",
    ]

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_gloucestershire.council_tax_reduction
        weekly_earnings = benunit(
            "south_gloucestershire_council_tax_reduction_weekly_earnings", period
        )
        return ctr.income_band.support_rate.calc(weekly_earnings)
