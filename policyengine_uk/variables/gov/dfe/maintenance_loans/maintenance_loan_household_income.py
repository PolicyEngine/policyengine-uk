from policyengine_uk.model_api import *
import numpy as np


class maintenance_loan_household_income(Variable):
    value_type = float
    entity = Person
    label = "Maintenance loan assessed household income"
    documentation = (
        "Student Finance England-style household income for maintenance loan assessment. "
        "This can be set explicitly in simulations. By default, the model uses a proxy: "
        "dependent students use sponsor income from a selected older household benefit unit, "
        "plus their own benefit-unit income; otherwise the model uses benefit-unit adjusted net income."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        in_higher_education = person("maintenance_loan_in_higher_education", period)
        has_sponsor = person("maintenance_loan_has_sponsor", period)
        sponsor_income = person("maintenance_loan_sponsor_income", period)
        is_couple = person.benunit("is_couple", period)
        is_household_head = person("is_household_head", period)
        is_parent = person("is_parent", period)
        tenure_holder = person.household.get_holder("tenure_type")
        has_explicit_tenure = (
            tenure_holder.get_array(period) is not None
            or tenure_holder.get_array(period.last_year) is not None
        )
        is_renting = (
            person.benunit("benunit_is_renting", period)
            if has_explicit_tenure
            else np.zeros_like(has_sponsor, dtype=bool)
        )
        benunit_income = person.benunit.sum(
            person.benunit.members("adjusted_net_income", period)
        )
        dependent_student_proxy = (
            in_higher_education
            & has_sponsor
            & np.logical_not(is_couple)
            & np.logical_not(is_household_head)
            & np.logical_not(is_parent)
            & np.logical_not(is_renting)
        )
        return where(
            dependent_student_proxy,
            sponsor_income + benunit_income,
            benunit_income,
        )
