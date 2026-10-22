from policyengine_uk.model_api import *


class spousal_maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "spousal maintenance income"
    documentation = (
        "Maintenance paid to this person by their spouse, civil partner, "
        "former spouse or former civil partner, under a court order, an "
        "agreement or voluntarily. Child maintenance is maintenance_income. "
        "Unlike child maintenance, this counts as income for Universal "
        "Credit, Pension Credit (but not as savings credit qualifying income), "
        "Income Support, Council Tax Reduction and Housing Benefit, and it is "
        "market and HBAI income as maintenance_income is."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/9",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/40",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
    )
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
