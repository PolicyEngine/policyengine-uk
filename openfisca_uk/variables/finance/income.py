from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = u"Income received from sublet agreements"
    definition_period = YEAR


class base_net_income(Variable):
    value_type = float
    entity = Person
    label = u"Existing net income for the person to use as a base in microsimulation"
    definition_period = YEAR


class net_income(Variable):
    value_type = float
    entity = Person
    label = u"Net income for the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        base = person("base_net_income", period)
        modelling = person("tax_modelling", period) + person("benefits_modelling", period)
        return base + modelling


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = u"Total amount of hours worked by this person"
    definition_period = WEEK


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = u"Average weekly hours for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("hours_worked", period, options=[ADD]) / WEEKS_IN_YEAR


class EmploymentStatus(Enum):
    FT_EMPLOYED = "Full-time employed"
    PT_EMPLOYED = "Part-time employed"
    FT_SELF_EMPLOYED = "Full-time self-employed"
    PT_SELF_EMPLOYED = "Part-time self-employed"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"
    STUDENT = "Student"
    CARER = "Carer"
    LONG_TERM_DISABLED = "Long-term sick/disabled"
    SHORT_TERM_DISABLED = "Short-term sick/disabled"
    OTHER_INACTIVE = "Inactive for another reason"
    CHILD = "Child"


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = u"Employment status of the person"
    definition_period = YEAR

class household_net_income(Variable):
    value_type = float
    entity = Household
    label = u"Household net income, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return max_(0, aggr(household, period, ["net_income"]) - household(
            "council_tax", period
        ))


class household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Household net income, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income", period) - household("housing_costs", period, options=[ADD])


class equiv_household_net_income(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised household net income, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income", period) / household(
            "household_equivalisation_bhc", period
        )


class equiv_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised household net income, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income_ahc", period) / household(
            "household_equivalisation_ahc", period
        )
