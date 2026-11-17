from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    in_other_non_liable_family,
)


class council_tax_reduction_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for CTR non-dependent deduction"
    documentation = (
        "A non-dependant aged 18 or over: an adult outside every family "
        "claiming Council Tax Reduction for the household who is not liable "
        "for rent, or a member of any family's benefit unit who is not its "
        "applicant, partner or a child or young person (see "
        "is_benefit_unit_non_dependant_for_council_tax_reduction), including "
        "a boarder's or lodger's adult son. Someone jointly and severally "
        "liable for the council tax with the applicant (a joint tenant or "
        "other sharer of the rent) and a boarder or lodger who pays the "
        "applicant are not non-dependants."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/9",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/3",
    )

    def formula(person, period, parameters):
        # SI 2012/2885 reg 9(2)(a), (c)-(e) and the Welsh and Scottish
        # equivalents; deductions are for non-dependants aged 18 or over.
        other_family = in_other_non_liable_family(person, period)
        # A member of any family's benefit unit who is not in its applicant's
        # family. Reg 9(2)(e) excludes only the person liable to pay the
        # applicant, so a boarder's or lodger's adult son is a non-dependant.
        in_unit = person(
            "is_benefit_unit_non_dependant_for_council_tax_reduction", period
        )
        return (person("age", period) >= 18) & (other_family | in_unit)
