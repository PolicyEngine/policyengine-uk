from policyengine_uk.model_api import *


class is_qualifying_young_person_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Universal Credit"
    documentation = (
        "A qualifying young person under UC Regs 2013 reg. 5 "
        "(is_qualifying_young_person_under_universal_credit_regulation_5): a "
        "person aged 16 to 19 who meets reg. 5(1)(a) or (b) and receives no "
        "Universal Credit, contributory ESA or contribution-based JSA (reg. "
        "5(5)) and no existing benefit: income-based JSA, income-related ESA, "
        "Income Support, Housing Benefit, Child Tax Credit or Working Tax "
        "Credit (SI 2014/1230 regs. 2(1) and 28; SR 2016/226 regs. 2(1) and "
        "29). The Secretary of State ties the exclusion to entitlement (reg. "
        "28), so the formula reads a report only while the model pays that "
        "benefit on it, and only if no reform neutralises it. The model pays "
        "Income Support, income-based JSA and tax credits only while "
        "gov.dwp.income_support.active, gov.dwp.JSA.income.active and "
        "gov.dwp.tax_credits.active hold, or while "
        "gov.contrib.policyengine.disable_simulated_benefits pays them as "
        "reported, and has no closure date for Housing Benefit or "
        "income-related ESA. The model also ends a person's legacy awards "
        "once its annual migration proxy closes them: it ends their Income "
        "Support, income-based JSA and income-related ESA when "
        "person_legacy_benefits_closed holds, and the family's Housing "
        "Benefit and tax credits when legacy_benefits_closed holds and the "
        "family doesn't meet the Pension Credit age conditions. The formula "
        "follows both closures. It doesn't follow the closures that read "
        "claims_universal_credit (esa_income_report_closed for a claimant or "
        "partner, housing_benefit_eligible and is_CTC_eligible), because "
        "claims_universal_credit reads this variable. The formula checks each "
        "report against its own variable: income_support, jsa_income, "
        "esa_income, housing_benefit, child_tax_credit or tax_credits for "
        "Child Tax Credit, and working_tax_credit or tax_credits for Working "
        "Tax Credit. A reform that changes or zeroes a benefit's formula "
        "without neutralising its variable leaves the exclusion on that "
        "benefit's reports in place. For a claimant or partner it also reads "
        "the couple's joint tax credit award (Tax Credits Act 2002 s.3(3)), "
        "each credit by its own check."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/2",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
    ]

    def formula(person, period, parameters):
        # The Secretary of State excludes a person entitled to an existing
        # benefit (TP regs. 2(1) and 28). The formula reads raw person-level
        # reports and the model's legacy closure proxy, so it calculates no
        # family benefit that depends on QYP status.
        p = parameters(period).gov
        dwp = p.dwp
        # The reform pays each benefit at its reported amount after the
        # model's closure dates, and holds both legacy closures false.
        paid_as_reported = p.contrib.policyengine.disable_simulated_benefits
        system = person.simulation.tax_benefit_system

        def paying(active, *names):
            # Nobody is entitled to a benefit the model no longer pays, or one
            # a reform neutralises.
            return bool(active or paid_as_reported) and not any(
                system.get_variable(name).is_neutralized for name in names
            )

        # The model ends a person's Income Support, income-based JSA and
        # income-related ESA when their legacy awards close: the claimant's
        # and partner's together (legacy_benefits_closed, read through
        # income_support), and anyone else's on their own reports
        # (jsa_income, esa_income). esa_income_report_closed also ends a
        # claimant's or partner's income-related ESA when the family claims
        # Universal Credit, but the formula can't read it: its
        # claimant-or-partner limb reads claims_universal_credit, which reads
        # this variable. person_legacy_benefits_closed and
        # legacy_benefits_closed read reports, is_claimant_or_partner, the
        # Pension Credit age conditions and parameters, and no Universal
        # Credit variable.
        own_award_open = ~person("person_legacy_benefits_closed", period)
        # The model pays Housing Benefit and tax credits to the family, on
        # every member's reports, and ends them when the claimant's and
        # partner's legacy awards close (housing_benefit_eligible,
        # is_CTC_eligible, is_WTC_eligible). A family that meets the Pension
        # Credit age conditions keeps Housing Benefit unless it leaves that
        # route by claiming Universal Credit, which the formula can't read,
        # so for such a family the formula keeps the Housing Benefit report.
        family_closed = person.benunit("legacy_benefits_closed", period)
        family_award_open = ~family_closed
        housing_benefit_open = ~(
            family_closed
            & ~person.benunit("meets_pension_credit_age_conditions", period)
        )

        income_support_paying = (
            paying(dwp.income_support.active, "income_support") & own_award_open
        )
        jsa_income_paying = paying(dwp.JSA.income.active, "jsa_income") & own_award_open
        esa_income_paying = paying(True, "esa_income") & own_award_open
        housing_benefit_paying = paying(True, "housing_benefit") & housing_benefit_open
        child_tax_credit_paying = (
            paying(dwp.tax_credits.active, "child_tax_credit", "tax_credits")
            & family_award_open
        )
        working_tax_credit_paying = (
            paying(dwp.tax_credits.active, "working_tax_credit", "tax_credits")
            & family_award_open
        )
        tax_credits_reported = child_tax_credit_paying * person(
            "child_tax_credit_reported", period
        ) + working_tax_credit_paying * person("working_tax_credit_reported", period)
        # Tax Credits Act 2002 s.3(3): the members of a couple claim jointly,
        # so the couple's award belongs to the claimant and the partner. A
        # dependant claims as a single person, so their award stays theirs.
        claimant_or_partner = person("is_claimant_or_partner", period)
        couple_tax_credits_reported = person.benunit.sum(
            where(claimant_or_partner, tax_credits_reported, 0)
        )
        receives_tax_credits = (tax_credits_reported > 0) | (
            claimant_or_partner & (couple_tax_credits_reported > 0)
        )
        entitled_to_existing_benefit = (
            (esa_income_paying & (person("esa_income_reported", period) > 0))
            | (jsa_income_paying & (person("jsa_income_reported", period) > 0))
            | (income_support_paying & (person("income_support_reported", period) > 0))
            | (
                housing_benefit_paying
                & (person("housing_benefit_reported", period) > 0)
            )
            | receives_tax_credits
        )
        return (
            person(
                "is_qualifying_young_person_under_universal_credit_regulation_5",
                period,
            )
            & ~entitled_to_existing_benefit
        )
