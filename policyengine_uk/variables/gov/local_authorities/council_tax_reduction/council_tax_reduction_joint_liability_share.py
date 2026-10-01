from policyengine_uk.model_api import *


class council_tax_reduction_joint_liability_share(Variable):
    value_type = float
    entity = BenUnit
    label = "Share of the council tax for a jointly liable Council Tax Reduction claim"
    documentation = (
        "Where the claimant is jointly and severally liable for the council "
        "tax with people other than their partner, the council tax used for "
        "the maximum reduction is divided by the number of people jointly and "
        "severally liable, and a deduction for a non-dependant of two or more "
        "of them is apportioned equally between them. The model takes the "
        "people liable for the household's rent as those jointly liable for "
        "its council tax (residents with the same interest, Local Government "
        "Finance Act 1992 s.6) and follows the regulations' wording, dividing "
        "by every person liable, the claimant's partner included. Students "
        "are not excluded from the count. Otherwise the share is one."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029",
        "https://www.legislation.gov.uk/ssi/2021/249",
    )

    def formula(benunit, period, parameters):
        # SI 2012/2885 Sch 1 para 7(3)-(4) and para 8(5); the Welsh and
        # Scottish schemes have the same wording.
        person = benunit.members
        liable = person("is_liable_for_household_rent", period)
        liable_people = benunit.max(person.household.sum(liable))
        in_family = benunit.sum(liable)
        jointly_with_others = (in_family > 0) & (liable_people > in_family)
        return where(jointly_with_others, 1 / max_(liable_people, 1), 1)
