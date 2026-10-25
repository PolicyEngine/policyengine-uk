"""Project the higher pension-age Housing Benefit personal allowances.

For claimants who reached State Pension age before 1 April 2021, SI 2006/214
Schedule 3 paragraph 1(1)(b) and (2)(b) set a personal allowance made up of
the Pension Credit standard minimum guarantee plus the maximum Savings Credit
(DWP circular HB A3/2021, paragraphs 3-5). Every published amount from
2019-20 to 2026-27 is that sum rounded up to the next 5p. The guarantee rises
with earnings and the maximum with September CPI, so neither index alone
projects the allowance. Keep the published allowances and derive later years
as the guarantee plus the maximum, each already uprated by its own index.

Run after general uprating and before fiscal-year conversion, on both the
main tree and its baseline copy, as the Savings Credit threshold projection
is. Reprocessing a reform then reads its changed guarantee and maximum.
"""

from policyengine_core.parameters import ParameterNode

from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    extend_after_last_stated,
    last_projected_year,
)

# The Pension Credit amounts each allowance is built from: a lone parent's
# are a single person's.
RELATIONS = {"single": "SINGLE", "couple": "COUPLE", "lone_parent": "SINGLE"}


def project_pension_age_allowances(parameters: ParameterNode) -> ParameterNode:
    """Fill the years after each higher allowance's last stated value."""
    pc = parameters.gov.dwp.pension_credit
    allowances = parameters.gov.dwp.housing_benefit.allowances
    last_year = last_projected_year(parameters)
    for kind, relation in RELATIONS.items():
        guarantee = pc.guarantee_credit.minimum_guarantee.children[relation]
        maximum = pc.savings_credit.maximum.children[relation]

        def derive(sample, previous):
            return guarantee(sample) + maximum(sample)

        extend_after_last_stated(allowances.children[kind].aged, last_year, derive)
    allowances.clear_parent_cache()
    return parameters
