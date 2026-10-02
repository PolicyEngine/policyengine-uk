from policyengine_uk.model_api import *
from policyengine_uk.utils.stochastic import splitmix64_uniform, stratified_uniform


class months_since_last_birthday(Variable):
    value_type = float
    entity = Person
    label = "months since last birthday"
    documentation = (
        "Months since the person's most recent birthday, at the middle of the "
        "fiscal year (6 October), from 0 up to 12. With age, this places the "
        "date of birth: the person was born age years and this many months "
        "before 6 October. A fractional age is read as the exact age on 6 "
        "October, whatever this is set to. For a whole age, simulations of a "
        "household situation use 6, "
        "the middle of the year of age. Microdata records age only in whole "
        "years, so in simulations built from data each single year of age and "
        "sex is spread evenly over the year: records are ordered by a "
        "deterministic hash of the person id and placed by their share of the "
        "group's weight. Datasets and situations can set this directly, and "
        "filter_dataset carries it into a household extracted from the data."
    )
    definition_period = YEAR
    unit = "month"
    # A situation that sets this for some people gives the rest the default
    # rather than the formula, so the default is the middle of the year too.
    default_value = 6

    def formula(person, period, parameters):
        age = person("age", period)
        whole_years = np.floor(age)
        fraction = age - whole_years
        if getattr(person.simulation, "built_from_dataset", False):
            position = stratified_uniform(
                strata=whole_years * 2 + person("is_male", period),
                draws=splitmix64_uniform(person("person_id", period), salt=2),
                weights=person("person_weight", period),
            )
        else:
            position = np.full(person.count, 0.5)
        return 12 * where(fraction > 0, fraction, position)
