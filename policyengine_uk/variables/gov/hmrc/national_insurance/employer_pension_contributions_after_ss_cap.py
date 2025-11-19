from policyengine_uk.model_api import *


class employer_pension_contributions_after_ss_cap(Variable):
    label = "Employer pension contributions after salary sacrifice cap behavioral response"
    documentation = """
    Total employer pension contributions after accounting for the behavioral
    response to the salary sacrifice pension cap.

    This equals:
    - Original employer pension contributions
    - MINUS: Reduction due to employers offsetting NI charges

    This variable models the real-world impact where employers reduce pension
    contributions to offset the additional 15% NI charge they face on salary
    sacrifice amounts exceeding £2,000.
    """
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.ft.com/content/11602ac1-44fc-4b58-8b17-af5e851f5c95"
    )

    def formula(person, period):
        # Original employer pension contributions
        original_contributions = person(
            "employer_pension_contributions", period
        )

        # Reduction due to behavioral response
        reduction = person("employer_pension_reduction_from_ss_cap", period)

        # Net contributions after behavioral response
        return max_(original_contributions - reduction, 0)
