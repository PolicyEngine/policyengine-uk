from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age CTR carer premium"
    documentation = (
        "The carer premium in a working-age Council Tax Reduction applicable "
        "amount. Outside Scotland's working-age scheme it equals carer_premium. "
        "In Scotland's scheme (SSI 2021/249 Sch 1 paras 5 and 6, from 1 April "
        "2022) councils pay it in respect of each applicant or partner who "
        "has regular and substantial caring responsibilities for a severely "
        "disabled person. The Scottish Ministers define those in para 6(1) "
        "as (a) receiving Carer's Allowance or Carer Support Payment, (b) "
        "being entitled to an allowance that DWP or Social Security Scotland "
        "reduces to nil under the overlapping benefits rules, or (c) having "
        "an award of Universal Credit which includes the carer element. "
        "carer_premium tests limbs (a) and (b) "
        "(is_entitled_to_carer_benefit). For limb (c), the Scottish Ministers "
        "defined an award of Universal Credit from 1 April 2022 to include "
        '"a universal credit award with a value of zero" (reg 4, as SSI '
        '2022/52 reg 3 amended it), and from 1 April 2025 as "an award of '
        'universal credit made under Part 1 of the 2012 Act" (SSI 2025/24 '
        "reg 8). An income that tapers the amount payable below one penny "
        "fails a financial condition of entitlement (Welfare Reform Act 2012 "
        "s.5(1)(b); UC Regs 2013 reg 17), so DWP makes no award or the award "
        "ends (UC Claims and Payments Regs 2013 reg 32A(1)), and there is no "
        "award to have a value of zero. The Scottish Government's policy "
        "note to SSI 2025/24 confines the earlier words to an award a "
        "sanction reduces to zero, and the Scottish Ministers inserted reg "
        "10A to bring part of the earnings case in from 1 April 2025. So in "
        "every year from 2022-23 the model reads limb (c) from the award "
        "itself (receives_uc_carer_element): an award of at least one penny "
        "that includes the carer element in respect of this claimant. For "
        "an award that earnings end, its last assessment period and any "
        "reclaim months from 2022-23 to 2024-25 remain arguable; the model "
        "cannot tell that award from a first claim, on which DWP makes no "
        "award. From 1 April "
        "2025 the Scottish Ministers also count two nil awards as awards (reg "
        "10A): one a sanction reduces to nil, and one whose claimant the "
        "Secretary of State treats as reclaiming after earnings end it (UC "
        "Claims and Payments Regs 2013 reg 32A). The model has neither "
        "sanctions nor reclaims, so it pays no premium for those, nor for "
        "a sanctioned nil award from 2022-23 to 2024-25. A person "
        "with both an allowance and a carer element qualifies once: councils "
        "include the premium for each applicant or partner who qualifies "
        "(paras 5(2) and (3)), not for each award. Partners caring for the "
        "same severely disabled person "
        "get one premium (para 5(3) and (4); "
        "partners_care_for_same_severely_disabled_person), as in "
        "carer_premium. Councils give it, under para 5(4), in respect of the "
        "one whose Universal Credit award includes the carer element first, "
        "then one in receipt of an allowance, then one entitled to an "
        "allowance reduced to nil; that choice does not change the amount. "
        "Before 1 April 2022 councils paid the premium to persons under "
        "pension age on entitlement to Carer's Allowance only (SSI 2012/303 "
        "Sch 1 para 14; carer_premium_counts_uc_carer_element). Scotland's "
        "working-age award reads council_tax_reduction_working_age_carers, "
        "which applies the same test to the applicant and partner."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/1",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4/2022-04-01",
        "https://www.legislation.gov.uk/ssi/2022/52/regulation/3/made",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4/2025-04-01",
        "https://www.legislation.gov.uk/ssi/2025/24/regulation/8/made",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/10A",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/14/2021-04-01",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/17",
        "https://www.legislation.gov.uk/uksi/2013/380/regulation/32A",
    )

    def formula(benunit, period, parameters):
        carer_premium = benunit("carer_premium", period)
        scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age
        if not scotland.carer_premium_counts_uc_carer_element:
            return carer_premium
        scottish_working_age = (
            benunit.household("country", period) == Country.SCOTLAND
        ) & ~benunit("council_tax_reduction_pensioner", period)
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # SSI 2021/249 Sch 1 para 6(1)(c): an award of Universal Credit which
        # includes the carer element. An earnings nil case has no award in
        # any year (Welfare Reform Act 2012 s.5(1)(b); reg 4 and reg 10A).
        carer_element_award = person("receives_uc_carer_element", period)
        # Para 6(1)(a) and (b), as in carer_premium, or (c).
        caring = person("is_entitled_to_carer_benefit", period) | carer_element_award
        qualifying_carers = benunit.sum(claimant_or_partner & caring)
        same_person = benunit("partners_care_for_same_severely_disabled_person", period)
        qualifying_carers = where(
            same_person, min_(qualifying_carers, 1), qualifying_carers
        )
        amount = parameters(period).gov.dwp.carer_premium.single
        return where(
            scottish_working_age,
            qualifying_carers * amount * WEEKS_IN_YEAR,
            carer_premium,
        )
