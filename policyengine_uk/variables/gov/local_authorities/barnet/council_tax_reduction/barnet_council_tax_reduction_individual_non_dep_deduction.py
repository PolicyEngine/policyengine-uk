from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_barnet_working_age,
)


class barnet_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Barnet CTS individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.barnet.council_tax_reduction
        household = person.household
        working_age = is_barnet_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("attendance_allowance", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
            )
        )
        gross_income = add(
            person,
            period,
            [
                "employment_income",
                "self_employment_income",
                "property_income",
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
                "state_pension",
            ],
        )
        weekly_gross_income = gross_income / WEEKS_IN_YEAR
        deduction = (
            ctr.non_dep_deduction.amount.calc(weekly_gross_income) * WEEKS_IN_YEAR
        )
        return working_age * where(claimant_exempt, 0.0, deduction)
