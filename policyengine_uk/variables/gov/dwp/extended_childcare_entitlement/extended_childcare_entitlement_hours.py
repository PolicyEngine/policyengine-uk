from policyengine_uk.model_api import *


class extended_childcare_entitlement_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "Hours of extended childcare entitlement"
    documentation = "Number of hours of extended childcare entitlement based on eligibility conditions"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Get parameters
        p = parameters(
            period
        ).gov.dwp.extended_childcare_entitlement.childcare_entitlement_hours

        # Check age conditions
        meets_first_age_condition = benunit.any(
            benunit.members(
                "extended_childcare_first_entitlement_age_condition", period
            ),
        )

        meets_second_age_condition = benunit.any(
            benunit.members(
                "extended_childcare_second_entitlement_age_condition", period
            ),
        )

        # Check income condition (same for both)
        meets_income_condition = benunit.all(
            benunit.members(
                "extended_childcare_entitlement_meets_income_requirements",
                period,
            )
            | benunit.members("is_child", period)
        )

        # Check work condition (same for both)
        work_eligible = benunit(
            "extended_childcare_entitlement_work_condition", period
        )

        # Calculate full eligibility for each entitlement
        first_entitlement = np.logical_and.reduce(
            [
                meets_first_age_condition,
                meets_income_condition,
                work_eligible,
            ]
        )

        second_entitlement = np.logical_and.reduce(
            [
                meets_second_age_condition,
                meets_income_condition,
                work_eligible,
            ]
        )

        # Return hours based on eligibility
        return select(
            [second_entitlement, first_entitlement, True],
            [p.second_entitlement, p.first_entitlement, 0.0],
        )
