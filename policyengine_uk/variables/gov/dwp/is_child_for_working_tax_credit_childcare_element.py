from policyengine_uk.model_api import *


class is_child_for_working_tax_credit_childcare_element(Variable):
    """Child whose childcare charges count for the WTC childcare element.

    Relevant childcare charges are for a child the claimant is responsible for
    (reg 14(1)). A person is a child until the last day of the week containing
    the 1 September after their 15th birthday, or 16th if disabled: receiving
    DLA or PIP, or certified blind (reg 14(3)-(4)). Annual ages approximate the
    September cut-off. Looked-after children are not a claimant's
    responsibility (Child Tax Credit Regulations 2002 reg 3).
    """

    value_type = bool
    entity = Person
    label = "Child for the Working Tax Credit childcare element"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/14",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/3",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.tax_credits.working_tax_credit.childcare_child_age_limit
        disabled = person("is_disabled_for_benefits", period) | person(
            "is_blind", period
        )
        age_limit = where(disabled, p.disabled, p.standard)
        return (
            ~person("is_claimant_or_partner", period)
            & ~person("is_looked_after_by_local_authority", period)
            & (person("age", period) < age_limit)
        )
