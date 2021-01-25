from openfisca_uk.tools.general import add
from openfisca_core.model_api import *
from openfisca_uk.entities import *


def ubi_reform(
    senior, adult, child, dis_1, dis_2, dis_3, geo, removed_benefits=[]
):
    """Create an OpenFisca-UK reform class.
    Args:
        senior (float): Pensioner UBI amount per week
        adult (float): Adult UBI amount per week
        child (float): Child UBI amount per week
        dis_1 (float): Disabled (Equality Act+) supplement per week
        dis_2 (float): Enhanced disabled supplement per week
        dis_3 (float): Severely disabled supplement per week
        geo (ndarray): Numpy float array of 12 UK regional supplements per week
    Returns:
        Reform: reform for a Simulation
    """

    class income_tax(Variable):
        value_type = float
        entity = Person
        label = "Income tax paid per year"
        definition_period = YEAR

        def formula(person, period, parameters):
            return 0.5 * person("taxable_income", period)

    class basic_income(Variable):
        value_type = float
        entity = Person
        label = "Amount of basic income received per week"
        definition_period = WEEK
    set_input = set_input_divide_by_period

        def formula(person, period, parameters):
            region = person.household("region", period)
            return (
                senior * person("is_SP_age", period.this_year)
                + adult * person("is_WA_adult", period.this_year)
                + child * person("is_child", period.this_year)
                + dis_1 * person("is_disabled", period.this_year)
                + dis_2 * person("is_enhanced_disabled", period.this_year)
                + dis_3 * person("is_severely_disabled", period.this_year)
                + geo[person.household("region").astype(int)]
            )

    class gross_income(Variable):
        value_type = float
        entity = Person
        label = "Gross income"
        definition_period = YEAR

        def formula(person, period, parameters):
            COMPONENTS = [
                "basic_income",
                "earnings",
                "profit",
                "state_pension",
                "pension_income",
                "savings_interest",
                "rental_income",
                "SSP",
                "SPP",
                "SMP",
                "holiday_pay",
                "dividend_income",
                "total_benefits",
                "benefits_modelling",
            ]
            return add(person, period, COMPONENTS, options=[MATCH])

    class reform(Reform):
        def apply(self):
            for changed_var in [income_tax, gross_income]:
                self.update_variable(changed_var)
            for added_var in [basic_income]:
                self.add_variable(added_var)
            for removed_var in removed_benefits + ["NI"]:
                self.neutralize_variable(removed_var)

    return reform
