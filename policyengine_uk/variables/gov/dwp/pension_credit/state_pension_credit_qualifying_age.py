from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_instant, grid_months_to_yyyymmdd
from policyengine_uk.utils.state_pension_age import age_attaining_pensionable_age


class state_pension_credit_qualifying_age(Variable):
    value_type = float
    entity = Person
    label = "qualifying age for State Pension Credit for this person"
    documentation = (
        "The age at which this person reaches the qualifying age for State "
        "Pension Credit: pensionable age for a woman, and for a man the "
        "pensionable age of a woman born on the same day. It differs from the "
        "person's own State Pension age only for men born before 6 December "
        "1953, whose pensionable age is 65. Universal Credit, Housing Benefit, "
        "Council Tax Reduction, Income Support and Winter Fuel Payment before "
        "September 2024 use this age as well as Pension Credit. The date of "
        "birth is date_of_birth where given, and otherwise comes from age and "
        "months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "year"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.state_pension.age
        birth = birth_instant(person, period)
        birth_date = grid_months_to_yyyymmdd(birth)
        # State Pension Credit Act 2002 s.1(6): "(a) in the case of a woman,
        # pensionable age; or (b) in the case of a man, the age which is
        # pensionable age in the case of a woman born on the same day as the
        # man". Every date of birth follows the women's timetable, so the male
        # rule in Pensions Act 1995 Sch 4 para 1 rule (1) never applies.
        return age_attaining_pensionable_age(
            p, birth, birth_date, male_rule=np.zeros(person.count, dtype=bool)
        )
