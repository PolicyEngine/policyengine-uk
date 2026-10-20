from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    charged_to_other_families,
    deduction_per_family,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._national_non_dependants import (
    household_head_family_is_pensioner,
    individual_non_dep_deduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants in other benefit units of the "
        "household: one per couple, the higher of the two members' amounts "
        "(both, in the Welsh scheme for people who are not pensioners, when "
        "the couple has a Universal Credit award), one for each other member, "
        "each under the applicant family's own scheme and apportioned between "
        "jointly liable applicants; none if the applicant or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        country = benunit.household("country", period)
        # WSI 2013/3029 Sch 6 para 5(3): a working-age applicant's deduction is
        # for each member of a non-dependant couple with a Universal Credit
        # award.
        universal_credit_couple = is_wales_scheme(country) & (
            benunit("universal_credit_pre_benefit_cap", period) > 0
        )
        # council_tax_reduction_individual_non_dep_deduction is each person's
        # deduction under the scheme of the household head's family. A jointly
        # liable applicant whose own family is under the other scheme (SI
        # 2012/2885 reg 3) has its deductions recomputed under that scheme.
        head_pensioner = household_head_family_is_pensioner(person, period)
        deductions = {
            "head": person(
                "council_tax_reduction_individual_non_dep_deduction", period
            ),
            "other": person(
                "council_tax_reduction_individual_non_dep_deduction_eligible", period
            )
            * individual_non_dep_deduction(person, period, parameters, ~head_pensioner),
        }
        head_family_pensioner = benunit.any(head_pensioner)
        charged = {}
        for scheme, amounts in deductions.items():
            pensioner = head_family_pensioner ^ (scheme == "other")
            deduction_for_benunit = deduction_per_family(
                benunit, period, amounts, universal_credit_couple & ~pensioner
            )
            # Each non-dependant family's amount counted once.
            charged[scheme] = charged_to_other_families(
                benunit, period, deduction_for_benunit
            )
        own_scheme_is_heads = (
            benunit("council_tax_reduction_pensioner", period) == head_family_pensioner
        )
        # A non-dependant of two or more jointly liable people is apportioned
        # equally between them (Sch 1 para 8(5)).
        share = benunit("council_tax_reduction_joint_liability_share", period)
        applicant_exempt = benunit(
            "council_tax_reduction_applicant_has_non_dep_exemption", period
        )
        return where(
            applicant_exempt,
            0,
            where(own_scheme_is_heads, charged["head"], charged["other"]) * share,
        )
