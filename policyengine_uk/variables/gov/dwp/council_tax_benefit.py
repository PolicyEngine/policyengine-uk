from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class council_tax_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Benefit"
    documentation = (
        "A family that claims gets the simulated reduction where the model "
        "simulates its own scheme, and its reported reduction otherwise. "
        "Where another claim in the household is simulated and pays a "
        "reduction on its share of the council tax, a jointly liable "
        "claimant's reported reduction is limited to its own share, so the "
        "two cannot together exceed the bill; the share is the one the "
        "simulated claims use. The share leaves out only people in higher "
        "education (in_HE), so where a jointly liable person it counts may be "
        "a student the law leaves out (the model's student test for "
        "non-dependants, or in_FE), the report is kept. That test reads "
        "current_education, which defaults to tertiary education at 18 and "
        "19, so with no education input a jointly liable 18- or 19-year-old "
        "keeps the cap off; part-time students and students the scheme brings "
        "back in are treated the same way. Otherwise reported reductions are "
        "kept as reported. A family that cannot claim keeps a reported "
        "reduction only where no claim in its household is simulated."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/4",
    )

    def formula(benunit, period, parameters):
        supported = benunit("council_tax_reduction_scheme_supported", period)
        simulated = benunit("simulated_council_tax_reduction_benunit", period)
        reported = benunit("council_tax_benefit_reported", period)
        claimant = benunit("council_tax_reduction_claimant_benunit", period)
        share = benunit("council_tax_reduction_joint_liability_share", period)
        household_simulates = benunit.household(
            "council_tax_reduction_household_has_simulated_claim", period
        )
        # Simulated reductions paid to claims in the household.
        person = benunit.members
        simulated_claim = (supported & claimant) * simulated
        paid_in_household = benunit.max(
            person.household.sum(
                person("is_benunit_head", period) * benunit.project(simulated_claim)
            )
        )
        # SI 2012/2885 Sch 1 para 7(3)-(4): a jointly liable claimant's
        # maximum reduction is on its share of the council tax. Applied only
        # beside a simulated claim that pays something, which uses the same
        # share; reports are otherwise kept.
        share_of_liability = (
            benunit.household(
                "council_tax_reduction_maximum_eligible_liability", period
            )
            * share
        )
        # Para 7(5) leaves students excluded from the scheme out of the
        # divisor. The share leaves out people in higher education (in_HE);
        # a jointly liable person it counts who may be a student (the
        # model's student test for non-dependants, or in_FE) could be left
        # out too, making the share too small, so the report is kept there.
        # The test reads current_education, whose age default puts 18- and
        # 19-year-olds in tertiary education; it does not tell full-time from
        # part-time study or find the students para 75(2) brings back in.
        counted_may_be_student = (
            person("council_tax_reduction_liable_person", period)
            & ~person("in_HE", period)
            & (is_full_time_student_non_dep(person, period) | person("in_FE", period))
        )
        share_may_count_student = (
            benunit.max(person.household.sum(counted_may_be_student)) > 0
        )
        reported_claim = where(
            (paid_in_household > 0) & (share < 1) & ~share_may_count_student,
            min_(reported, share_of_liability),
            reported,
        )
        not_claiming = where(household_simulates, 0, reported)
        return where(
            claimant, where(supported, simulated, reported_claim), not_claiming
        )
