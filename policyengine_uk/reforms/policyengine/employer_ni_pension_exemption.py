from policyengine_core.model_api import *
from policyengine_uk.model_api import Person, YEAR, GBP, WEEKS_IN_YEAR


def create_employer_ni_pension_exemption() -> Reform:
    """
    Reform that exempts employer pension contributions from employer NI.

    Policy: By default, employer pension contributions are included in
    taxed earnings for NI Class 1 employer calculations. This reform
    removes them from the calculation when exemption is active.
    """

    class ni_class_1_employer(Variable):
        value_type = float
        entity = Person
        label = "NI Class 1 employer-side contributions"
        definition_period = YEAR
        unit = GBP
        defined_for = "ni_liable"
        reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/9"

        def formula(person, period, parameters):
            class_1 = parameters(period).gov.hmrc.national_insurance.class_1
            earnings = person("ni_class_1_income", period)
            # Exempt employer pension contributions (don't add them)
            taxed_earnings = earnings
            secondary_threshold = (
                class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR
            )
            main_earnings = max_(
                taxed_earnings - secondary_threshold,
                0,
            )
            return class_1.rates.employer * main_earnings

    class reform(Reform):
        def apply(self):
            self.update_variable(ni_class_1_employer)

    return reform


def create_employer_ni_pension_exemption_reform(
    parameters, period, bypass: bool = False
):
    if bypass:
        return create_employer_ni_pension_exemption()

    if parameters(
        period
    ).gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions:
        return create_employer_ni_pension_exemption()
    else:
        return None


# For direct import
employer_ni_pension_exemption_reform = create_employer_ni_pension_exemption()
