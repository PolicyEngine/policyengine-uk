from policyengine_uk.model_api import *


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "maintenance payment income"
    documentation = (
        "Child maintenance received. It counts as market and HBAI income but "
        "is normally disregarded in claimant means tests. It is included in "
        "non-dependants’ gross income for Housing Benefit and Council Tax "
        "Reduction: their non-dependant disregards do not exempt child "
        "maintenance. Maintenance from a spouse, civil partner, former "
        "spouse or former civil partner is spousal_maintenance_income, which "
        "the means tests count."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
