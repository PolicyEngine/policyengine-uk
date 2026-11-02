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
        "29). Reg. 28 turns on entitlement, so the formula reads a person's own "
        "report of Income Support, income-based JSA or a tax credit only in a "
        "year the model pays that benefit (gov.dwp.income_support.active, "
        "gov.dwp.JSA.income.active, gov.dwp.tax_credits.active) and no reform "
        "neutralises it. It reads Housing Benefit and income-related ESA "
        "reports in every year. For a claimant or partner it also reads the "
        "couple's joint tax credit award (Tax Credits Act 2002 s.3(3))."
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
        # TP reg. 28 excludes a person entitled to an existing benefit (TP
        # reg. 2(1)). The formula reads raw person-level reports, so it
        # calculates no family benefit that depends on QYP status. It reads a
        # dependant's own reports, never a parent's.
        dwp = parameters(period).gov.dwp
        system = person.simulation.tax_benefit_system

        def paying(active, name):
            # Nobody is entitled to a benefit the model no longer pays, or one
            # a reform neutralises.
            return bool(active) and not system.get_variable(name).is_neutralized

        income_support_paying = paying(dwp.income_support.active, "income_support")
        jsa_income_paying = paying(dwp.JSA.income.active, "jsa_income")
        tax_credits_paying = paying(dwp.tax_credits.active, "tax_credits")
        tax_credits_reported = tax_credits_paying * (
            person("child_tax_credit_reported", period)
            + person("working_tax_credit_reported", period)
        )
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
            (person("esa_income_reported", period) > 0)
            | (jsa_income_paying & (person("jsa_income_reported", period) > 0))
            | (income_support_paying & (person("income_support_reported", period) > 0))
            | (person("housing_benefit_reported", period) > 0)
            | receives_tax_credits
        )
        return (
            person(
                "is_qualifying_young_person_under_universal_credit_regulation_5",
                period,
            )
            & ~entitled_to_existing_benefit
        )
