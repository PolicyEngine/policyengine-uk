from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age CTR carer premium"
    documentation = (
        "The carer premium in a working-age Council Tax Reduction applicable "
        "amount. Outside Scotland's working-age scheme it is carer_premium. "
        "Scotland's scheme (SSI 2021/249 Sch 1 paras 5 and 6, from 1 April "
        "2022) pays it in respect of each applicant or partner who has "
        "regular and substantial caring responsibilities for a severely "
        "disabled person. Para 6(1) defines those as (a) receiving Carer's "
        "Allowance or Carer Support Payment, (b) being entitled to one that "
        "the overlapping benefits rules reduce to nil, or (c) having an award "
        "of Universal Credit which includes the carer element. Limbs (a) and "
        "(b) are carer_premium's test (is_entitled_to_carer_benefit); limb (c) "
        "is receives_uc_carer_element, which needs a positive award, since an "
        "income that tapers the award to nil leaves no award (Welfare Reform "
        "Act 2012 s.5(1)(b), UC Regs 2013 reg 17). A person with both an "
        "allowance and a carer element qualifies once: the premium is for each "
        "partner who qualifies (para 5(3)), not for each award. Partners "
        "caring for the same severely disabled person get one premium (para "
        "5(3) and (4); partners_care_for_same_severely_disabled_person), as in "
        "carer_premium. Para 5(4) then pays it in respect of the one whose "
        "Universal Credit award includes the carer element, then one in "
        "receipt of an allowance, then one entitled to an allowance reduced "
        "to nil; that choice does not change the amount. Before 1 April 2022 "
        "the scheme for persons under pension age, SSI 2012/303 Sch 1 para "
        "14, tested entitlement to Carer's Allowance only "
        "(carer_premium_counts_uc_carer_element)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/1",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/14/2021-04-01",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
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
        # SSI 2021/249 Sch 1 para 6(1)(a) and (b), as in carer_premium, or
        # (c) an award of Universal Credit which includes the carer element.
        caring = person("is_entitled_to_carer_benefit", period) | person(
            "receives_uc_carer_element", period
        )
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
