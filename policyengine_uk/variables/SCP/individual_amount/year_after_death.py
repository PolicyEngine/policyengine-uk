class year_after_death(Variable):
    entity = Person
    label = "Year after death"
    definition_period = YEAR
    value_type = int

    def formula(person, period, parameters):
        # not completed
        return -1
