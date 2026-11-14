from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_earnings_income_tax import (
    DECISION,
    PRE_CHARGE_TAX,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    applicant_has_universal_credit,
)
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_tax_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction deduction for income tax and National Insurance"
    documentation = (
        "Income tax and National Insurance that Council Tax Reduction income "
        "deducts, for the applicant and partner "
        "(is_council_tax_reduction_applicant_or_partner). T is their income "
        "tax before the winter fuel payment charge, and T(X) the same with "
        "every person's X set to nil (pension_credit_income_tax_without_"
        "employment_income, pension_credit_income_tax_without_earnings and "
        "council_tax_reduction_income_tax_on_other_counted_income). E is "
        "employed earnings: employment income and statutory sick, maternity "
        "and paternity pay. S is self-employment income. U is the taxed "
        "income the pensioner schemes do not count, such as interest, "
        "dividends and rent from property. "
        "Scotland's working-age scheme (SSI 2021/249) deducts tax from "
        "earnings only. Where the applicant has no award of Universal Credit "
        "(council_tax_reduction_universal_credit_award, which includes an "
        "award the benefit cap or deductions reduce to nil), the formula "
        "deducts T less T(E), never negative, primary Class 1 "
        "contributions, and the notional tax and contributions on profit "
        "(council_tax_reduction_scotland_self_employment_deductions; reg "
        "51(9)). With an award it deducts T less T(E, S), never "
        "negative, and the Class 1, 2 and 4 contributions charged (regs "
        "49(6)(b) and 51(2) step 3). The pensioner schemes of England (SI "
        "2012/2885), Wales (WSI 2013/3029) and Scotland (SSI 2012/319) "
        "disregard the tax deducted from earnings and the tax payable on "
        "income taken into account, so the formula deducts T less T(E), "
        "never negative; T(E, S, U), the tax on the other counted income "
        "with the uncounted income above it and without the Step 7 charges in "
        "income_tax_charges (through the High Income Child Benefit Charge, "
        "HMRC recovers Child Benefit, which these schemes do not count, and "
        "the pension annual allowance charge falls on contributions, so the "
        "formula treats neither as tax payable on income taken into "
        "account); the notional tax and "
        "contributions on profit (pension_credit_self_employment_deductions "
        "in England and Wales, the Scottish variable in Scotland); and "
        "primary Class 1 contributions. Earnings are the top slice of income "
        "and self-employed profit sits beneath them, so the tax on earnings "
        "includes any tax they add on savings and dividends and through the "
        "marriage allowance. Benefits in kind stay in both terms of each "
        "difference, since no scheme counts a payment in kind as earnings. "
        "In the English and Welsh working-age schemes, and for families "
        "outside Great Britain, the formula deducts what the legacy means "
        "tests deduct: the applicant's and partner's "
        "legacy_means_test_deducted_income_tax, with their sum floored at "
        "nil, and all their National Insurance. With an award of Universal "
        "Credit, those schemes do not count rent from boarders, lodgers and "
        "sub-tenants in the home, so the formula first takes off the tax "
        "that rent would bear without earnings "
        "(rent_a_room_income_tax_without_earnings). " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/49",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/50",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/51",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/31",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/33",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/37",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/19",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/30",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/24",
    ]

    def formula(benunit, period, parameters):
        person = benunit.members
        members = person("is_council_tax_reduction_applicant_or_partner", period)

        def total(values):
            return benunit.sum(values * members)

        country = benunit.household("country", period)
        scotland = country == Country.SCOTLAND
        in_great_britain = (
            (country == Country.ENGLAND) | scotland | (country == Country.WALES)
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        pensioner_scheme = in_great_britain & pensioner
        scottish_working_age = scotland & ~pensioner
        with_universal_credit = scottish_working_age & applicant_has_universal_credit(
            benunit, period
        )
        without_universal_credit = scottish_working_age & ~with_universal_credit

        income_tax = person(PRE_CHARGE_TAX, period)
        tax = total(income_tax)
        class_1 = total(person("ni_class_1_employee", period))
        zeros = np.zeros_like(tax)

        # The other schemes deduct what the legacy means tests deduct: the
        # applicant's and partner's legacy_means_test_deducted_income_tax,
        # whose sum the formula floors at nil because one member's value can
        # turn negative where another's earnings move a Step 7 charge off
        # them, and all their National Insurance.
        other_schemes = ~(
            with_universal_credit | without_universal_credit | pensioner_scheme
        )
        if other_schemes.any():
            # Where a working-age applicant's award of Universal Credit keeps
            # rent out of the income, the formula leaves out the tax the rent
            # would bear without earnings and keeps the extra tax earnings
            # cause on it.
            uncounted_rent_tax = where(
                ~pensioner & applicant_has_universal_credit(benunit, period),
                total(person("rent_a_room_income_tax_without_earnings", period)),
                0,
            )
            legacy_deduction = max_(
                0,
                total(person("legacy_means_test_deducted_income_tax", period))
                - uncounted_rent_tax,
            ) + total(person("national_insurance", period))
        else:
            legacy_deduction = zeros

        # Each branch of income tax is read only where a scheme uses it.
        if (without_universal_credit | pensioner_scheme).any():
            tax_without_employment = total(
                person("pension_credit_income_tax_without_employment_income", period)
            )
        else:
            tax_without_employment = tax
        tax_on_employed_earnings = max_(0, tax - tax_without_employment)

        if with_universal_credit.any():
            tax_without_earnings = total(
                person("pension_credit_income_tax_without_earnings", period)
            )
        else:
            tax_without_earnings = tax
        uc_deduction = (
            max_(0, tax - tax_without_earnings)
            + class_1
            + total(add(person, period, ["ni_class_2", "ni_class_4"]))
        )

        scottish_notional = (
            total(
                person(
                    "council_tax_reduction_scotland_self_employment_deductions",
                    period,
                )
            )
            if (scotland & (without_universal_credit | pensioner_scheme)).any()
            else zeros
        )
        no_uc_deduction = tax_on_employed_earnings + class_1 + scottish_notional

        if pensioner_scheme.any():
            tax_on_other_counted_income = total(
                person(
                    "council_tax_reduction_income_tax_on_other_counted_income",
                    period,
                )
            )
            # The formula prices the English and Welsh notional tax with
            # Pension Credit's variable, because the Secretary of State and
            # the Welsh Ministers allow the same personal reliefs (SI
            # 2012/2885 Sch 1 para 30; WSI 2013/3029 Sch 1 para 24): those
            # under ITA 2007 Part 3 Chapters 2, 3 and 3A.
            england_and_wales_notional = total(
                person("pension_credit_self_employment_deductions", period)
            )
        else:
            tax_on_other_counted_income = zeros
            england_and_wales_notional = zeros
        notional = where(scotland, scottish_notional, england_and_wales_notional)
        pensioner_deduction = (
            tax_on_employed_earnings + tax_on_other_counted_income + notional + class_1
        )

        return select(
            [with_universal_credit, without_universal_credit, pensioner_scheme],
            [uc_deduction, no_uc_deduction, pensioner_deduction],
            default=legacy_deduction,
        )
