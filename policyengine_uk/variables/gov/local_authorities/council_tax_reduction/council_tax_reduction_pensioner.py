from policyengine_uk.model_api import *


class council_tax_reduction_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Pensioner for Council Tax Reduction"
    documentation = (
        "Whether the family's claim falls under the pension-age Council Tax "
        "Reduction rules: the claimant or partner has reached the qualifying "
        "age for State Pension Credit, and neither of them is on "
        "Income Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance, or has an award of Universal Credit. "
        "A mixed-age couple on Universal Credit is therefore not a pensioner in "
        "England, Wales or Scotland. English schemes are routed on this test, "
        "and Welsh and Scottish claims that fail it take the working-age rules."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/12",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/12",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_uc_claimant", period)
        # Either member of a couple can claim, so the older one can claim as a
        # pensioner. is_SP_age stands in for the qualifying age for State
        # Pension Credit, as elsewhere in the model.
        over_qualifying_age = person("is_SP_age", period)
        attained_qualifying_age = benunit.any(claimant_or_partner & over_qualifying_age)
        income_related_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        # The award before the benefit cap: the cap reduces an award
        # (UC Regs 2013 reg 81) rather than removing it. An award counts only
        # where a claimant or partner is under the qualifying age, which
        # Universal Credit needs (UC Regs 2013 reg 3(2)(a)); is_uc_eligible
        # counts any working-age adult, including a qualifying young person.
        # This also stands in for the rules that disregard an award held after
        # both members reach the qualifying age (SI 2012/2885 reg 3(2);
        # WSI 2013/3029 reg 3(2); SSI 2021/249 reg 3(2)). England and Wales
        # also disregard a tax credit migrant's award (UC (TP) Regs 2014 reg
        # 60A) and Scotland does not; the model has no such awards. The guard
        # relies on is_uc_claimant, which needs is_parent to recognise a
        # qualifying young person as a dependant.
        working_age_claimant = benunit.any(claimant_or_partner & ~over_qualifying_age)
        universal_credit_award = (
            benunit("is_uc_entitled", period) & working_age_claimant
        )
        return (
            attained_qualifying_age & ~income_related_benefit & ~universal_credit_award
        )
