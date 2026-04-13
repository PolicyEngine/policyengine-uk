from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)
from policyengine_uk.variables.gov.dfe.maintenance_loans.maintenance_loan_living_arrangement import (
    MaintenanceLoanLivingArrangement,
)


class maintenance_loan_household_income(Variable):
    value_type = float
    entity = Person
    label = "Maintenance loan assessed household income"
    documentation = (
        "Student Finance England-style household income for maintenance loan assessment. "
        "This can be set explicitly in simulations. By default, the model uses a proxy: "
        "students living with parents use older non-student household adults plus their own benefit-unit income; "
        "students living away from home use benefit-unit adjusted net income."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        arrangement = person("maintenance_loan_living_arrangement", period)
        household = person.household

        members_age = household.members("age", period)
        members_education = household.members("current_education", period)
        members_income = household.members("adjusted_net_income", period)

        parent_proxy_income = household.sum(
            ((members_age >= 30) & (members_education != EducationType.TERTIARY))
            * members_income
        ) + person.benunit.sum(person.benunit.members("adjusted_net_income", period))

        benunit_income = person.benunit.sum(
            person.benunit.members("adjusted_net_income", period)
        )

        return where(
            arrangement == MaintenanceLoanLivingArrangement.LIVING_WITH_PARENTS,
            parent_proxy_income,
            benunit_income,
        )
