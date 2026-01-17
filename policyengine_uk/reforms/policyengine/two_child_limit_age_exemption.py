from policyengine_core.model_api import *
from policyengine_uk.model_api import Person, YEAR, MONTHS_IN_YEAR, GBP
from numpy import inf, select, where


def create_two_child_limit_age_exemption(
    ctc_age_exemption: int = 0, uc_age_exemption: int = 0
) -> Reform:
    """
    Reform that applies age-based exemptions to the two-child limit for
    Child Tax Credit and Universal Credit.

    Policy: Exempt families from the two-child limit when they have a child
    under a specified age threshold.

    Args:
        ctc_age_exemption: Age threshold for CTC exemption (0 = no exemption)
        uc_age_exemption: Age threshold for UC exemption (0 = no exemption)
    """

    class is_CTC_child_limit_exempt(Variable):
        value_type = bool
        entity = Person
        label = "Exemption from Child Tax Credit child limit"
        documentation = "Exemption from Child Tax Credit limit on number of children based on birth year"
        definition_period = YEAR

        def formula(person, period, parameters):
            limit_year = parameters(
                period
            ).gov.dwp.tax_credits.child_tax_credit.limit.start_year
            # Children must be born before April 2017.
            # We use < 2017 as the closer approximation than <= 2017.
            born_before_limit = person("birth_year", period) < limit_year

            # Age exemption from reform
            if ctc_age_exemption > 0:
                is_exempt = person.benunit.any(
                    person("age", period) < ctc_age_exemption
                )
                return born_before_limit | is_exempt

            return born_before_limit

    class uc_individual_child_element(Variable):
        value_type = float
        entity = Person
        label = "Universal Credit child element"
        documentation = "For this child, given Universal Credit eligibility"
        definition_period = YEAR
        unit = GBP

        def formula(person, period, parameters):
            p = parameters(period).gov.dwp.universal_credit.elements.child
            child_index = person("child_index", period)
            born_before_limit = person(
                "uc_is_child_born_before_child_limit", period
            )
            child_limit_applying = where(
                ~born_before_limit, p.limit.child_count, inf
            )
            is_eligible = (child_index != -1) & (
                child_index <= child_limit_applying
            )

            # Age exemption from reform
            effective_born_before_limit = born_before_limit
            if uc_age_exemption > 0:
                is_exempt = person.benunit.any(
                    person("age", period) < uc_age_exemption
                )
                effective_born_before_limit = is_exempt

            return (
                select(
                    [
                        (child_index == 1)
                        & effective_born_before_limit
                        & is_eligible,
                        is_eligible,
                    ],
                    [
                        p.first.higher_amount,
                        p.amount,
                    ],
                    default=0,
                )
                * MONTHS_IN_YEAR
            )

    class reform(Reform):
        def apply(self):
            if ctc_age_exemption > 0:
                self.update_variable(is_CTC_child_limit_exempt)
            if uc_age_exemption > 0:
                self.update_variable(uc_individual_child_element)

    return reform


def create_two_child_limit_age_exemption_reform(
    parameters, period, bypass: bool = False
):
    """
    Create a two-child limit age exemption reform based on parameters.

    Args:
        parameters: The parameter tree
        period: The time period
        bypass: If True, always create the reform (used for direct application)

    Returns:
        A reform class or None if no exemptions are enabled
    """
    ctc_age = parameters(
        period
    ).gov.contrib.two_child_limit.age_exemption.child_tax_credit
    uc_age = parameters(
        period
    ).gov.contrib.two_child_limit.age_exemption.universal_credit

    if bypass or ctc_age > 0 or uc_age > 0:
        return create_two_child_limit_age_exemption(
            ctc_age_exemption=ctc_age, uc_age_exemption=uc_age
        )
    return None


# For direct import with default (no exemption)
two_child_limit_age_exemption_reform = create_two_child_limit_age_exemption()

# Preset reforms for testing with age exemption of 3
uc_age_exemption_3_reform = create_two_child_limit_age_exemption(
    uc_age_exemption=3
)
ctc_age_exemption_3_reform = create_two_child_limit_age_exemption(
    ctc_age_exemption=3
)
