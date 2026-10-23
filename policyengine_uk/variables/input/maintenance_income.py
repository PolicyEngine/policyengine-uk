from policyengine_uk.model_api import *


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "maintenance payment income"
    documentation = (
        "Child maintenance received. It counts as market and HBAI income but "
        "in no means test. Maintenance from a spouse, civil partner, former "
        "spouse or former civil partner is spousal_maintenance_income, which "
        "the means tests count."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
