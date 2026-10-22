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
        "applicant are not non-dependants. Those exclusions belong to the "
        "person, whatever family they are in: a person the model treats as "
        "liable for the council tax (council_tax_reduction_liable_person), "
        "and a person outside the household head's family who pays the "
        "householder for their own board or lodging, is nobody's "
        "non-dependant. A member of the household head's own family who pays "
        "board is taken to be a close relative of the head, so remains a "
        "non-dependant. The model has no relationship input, so a close "
        "relative in another family who pays board or lodging, or someone "
        "paying on a non-commercial basis, is treated as excluded, although "
        "the schemes make them non-dependants."
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
        # Reg 9(2)(d)-(e) exclude the person, not only their family. Anyone
        # treated as liable for the council tax (LGFA 1992 s.6) is jointly
        # and severally liable with the applicant. Anyone who pays the
        # householder for their own board or lodging is liable to make
        # payments on a commercial basis, even where the rest of their family
        # pays nothing, unless they are a close relative of the applicant or
        # partner or the agreement is not commercial (reg 9(3)(a)). The model
        # has no relationship input: a member of the household head's own
        # family who pays board is taken to be a close relative, and anyone
        # else who pays as excluded.
        pays_householder = (
            add(person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"]) > 0
        )
        in_head_family = person.benunit("benunit_contains_household_head", period)
        personally_excluded = person("council_tax_reduction_liable_person", period) | (
            pays_householder & ~in_head_family
        )
        return (
            (person("age", period) >= 18)
            & (other_family | in_unit)
            & ~personally_excluded
        )
