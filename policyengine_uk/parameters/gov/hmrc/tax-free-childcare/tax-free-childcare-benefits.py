from policyengine_uk.model_api import *

class tax_free_childcare_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax-free childcare support amount"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.tax_free_childcare

        # Check eligibility conditions from your YAML files
        meets_age_condition = benunit("child_age_eligible", period)
        meets_income_condition = benunit("meets_income_requirements", period)
        meets_work_condition = benunit("childcare_work_condition", period)
        meets_incompatibility = benunit("incompatibilities_childcare_eligible", period)

        # Check income threshold (£100,000)
        partner_1_income = benunit("yearly_eligible_income_p1", period)
        partner_2_income = benunit("yearly_eligible_income_p2", period)
        income_eligible = (partner_1_income <= p.income_threshold) & (partner_2_income <= p.income_threshold)

        # Get child counts
        num_standard_children = benunit("benunit_num_standard_children", period)
        num_disabled_children = benunit("benunit_num_disabled_children", period)

        # Calculate maximum amounts (£2,000 per standard child, £4,000 per disabled child)
        standard_max = num_standard_children * p.standard_child.yearly_max
        disabled_max = num_disabled_children * p.disabled_child.yearly_max
        total_max = standard_max + disabled_max

        # Get parent contribution and calculate government contribution (£2 for every £8)
        parent_contribution = benunit("childcare_parent_contribution", period)
        gov_contribution = (parent_contribution / p.government_contribution.parent_contribution) * p.government_contribution.gov_contribution

        # Cap the government contribution at maximum allowed
        capped_contribution = min_(gov_contribution, total_max)

        # Apply all eligibility conditions
        eligible = (
            meets_age_condition &
            meets_income_condition &
            meets_work_condition &
            meets_incompatibility &
            income_eligible
        )

        return where(
            eligible,
            capped_contribution,
            0
        )