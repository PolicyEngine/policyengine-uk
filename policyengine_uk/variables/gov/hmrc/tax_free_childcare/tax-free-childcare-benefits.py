from policyengine_uk.model_api import * 


def formula(benunit, period, parameters, parents_contribution):
    # Define tax-free childcare parameters
    p = {
        "standard_child": {
            "yearly_max": 2000
        },
        "disabled_child": {
            "yearly_max": 4000
        },
        "government_contribution": 2/8 
    }

    # Check eligibility conditions
    meets_age_condition = benunit("child_age_eligible", period)
    meets_income_condition = benunit.any(benunit.members("meets_income_requirements", period))
    is_eligible = meets_age_condition & meets_income_condition & benunit("incompatibilities_childcare_eligible", period)

    # Determine the maximum eligible childcare cost for a single child
    max_amount = 0
    for child in benunit.members("is_child", period):
        if is_eligible[child]:
            if child("is_disabled", period):
                max_amount = p["disabled_child"]["yearly_max"]  # Only consider disabled child's max
            else:
                max_amount = p["standard_child"]["yearly_max"]  # Only consider standard child's max

    # Calculate the government contribution
    government_contribution = min(parents_contribution * p["government_contribution"], max_amount)

    return government_contribution
