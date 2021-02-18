from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


ACCOUNTS = [
    "current_account",
    "NSI_direct_saver",
    "NSI_investment",
    "savings_and_investment",
    "GGES",
    "unit_or_inv_trusts",
    "stocks_and_shares",
    "PEP",
    "NS_capital_bonds",
    "ILNSC",
    "FINSC",
    "PGB",
    "SAYE",
    "premium_bonds",
    "NS_income_bonds",
    "NS_deposit_bonds",
    "first_option_bonds",
    "yearly_plan",
    "ISA",
    "profit_sharing",
    "CSOP",
    "member_of_share_club",
    "guaranteed_income",
    "GEB",
    "basic_account",
    "credit_unions",
    "EPNL",
    "post_office_card_account",
]

INTEREST_ACCOUNTS = [
    "current_account",
    "NSI_direct_saver",
    "NSI_investment",
    "savings_and_investment",
    "GGES",
    "PEP",
    "NS_capital_bonds",
    "ILNSC",
    "FINSC",
    "PGB",
    "SAYE",
    "premium_bonds",
    "NS_income_bonds",
    "NS_deposit_bonds",
    "first_option_bonds",
    "yearly_plan",
    "ISA",
    "profit_sharing",
    "CSOP",
    "guaranteed_income",
    "GEB",
    "basic_account",
    "EPNL",
    "post_office_card_account",
]

DIVIDEND_ACCOUNTS = [
    "unit_or_inv_trusts",
    "credit_unions",
    "stocks_and_shares",
    "member_of_share_club",
]


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of income from dividend-paying accounts"
    definition_period = YEAR

    def formula(person, period, parameters):
        return add(
            person,
            period,
            map(lambda name: name + "_income", DIVIDEND_ACCOUNTS),
        )


class taxable_dividend_income(Variable):
    value_type = float
    entity = Person
    label = u"Taxable income from dividends"
    definition_period = YEAR

    def formula(person, period, parameters):
        total = np.zeros_like(person("current_account_income", period))
        for account in DIVIDEND_ACCOUNTS:
            total += person(account + "_income", period) * person(
                account + "_pre_tax", period
            )
        return total


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of income from savings interest"
    definition_period = YEAR

    def formula(person, period, parameters):
        return add(
            person,
            period,
            map(lambda name: name + "_income", INTEREST_ACCOUNTS),
        )


class taxable_savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u"Taxable income from dividends"
    definition_period = YEAR

    def formula(person, period, parameters):
        total = np.zeros_like(person("current_account_income", period))
        for account in INTEREST_ACCOUNTS:
            total += person(account + "_income", period) * person(
                account + "_pre_tax", period
            )
        return total


class current_account_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of current_account"
    definition_period = YEAR


class current_account_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from current_account"
    definition_period = YEAR


class current_account_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether current_account income is pre-tax"
    definition_period = YEAR


class current_account_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether current_account is a joint account"
    definition_period = YEAR


class NSI_direct_saver_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of NSI_direct_saver"
    definition_period = YEAR


class NSI_direct_saver_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from NSI_direct_saver"
    definition_period = YEAR


class NSI_direct_saver_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NSI_direct_saver income is pre-tax"
    definition_period = YEAR


class NSI_direct_saver_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NSI_direct_saver is a joint account"
    definition_period = YEAR


class NSI_investment_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of NSI_investment"
    definition_period = YEAR


class NSI_investment_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from NSI_investment"
    definition_period = YEAR


class NSI_investment_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NSI_investment income is pre-tax"
    definition_period = YEAR


class NSI_investment_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NSI_investment is a joint account"
    definition_period = YEAR


class savings_and_investment_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of savings_and_investment"
    definition_period = YEAR


class savings_and_investment_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from savings_and_investment"
    definition_period = YEAR


class savings_and_investment_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether savings_and_investment income is pre-tax"
    definition_period = YEAR


class savings_and_investment_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether savings_and_investment is a joint account"
    definition_period = YEAR


class GGES_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of GGES"
    definition_period = YEAR


class GGES_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from GGES"
    definition_period = YEAR


class GGES_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether GGES income is pre-tax"
    definition_period = YEAR


class GGES_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether GGES is a joint account"
    definition_period = YEAR


class unit_or_inv_trusts_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of unit_or_inv_trusts"
    definition_period = YEAR


class unit_or_inv_trusts_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from unit_or_inv_trusts"
    definition_period = YEAR


class unit_or_inv_trusts_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether unit_or_inv_trusts income is pre-tax"
    definition_period = YEAR


class unit_or_inv_trusts_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether unit_or_inv_trusts is a joint account"
    definition_period = YEAR


class stocks_and_shares_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of stocks_and_shares"
    definition_period = YEAR


class stocks_and_shares_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from stocks_and_shares"
    definition_period = YEAR


class stocks_and_shares_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether stocks_and_shares income is pre-tax"
    definition_period = YEAR


class stocks_and_shares_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether stocks_and_shares is a joint account"
    definition_period = YEAR


class PEP_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of PEP"
    definition_period = YEAR


class PEP_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from PEP"
    definition_period = YEAR


class PEP_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether PEP income is pre-tax"
    definition_period = YEAR


class PEP_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether PEP is a joint account"
    definition_period = YEAR


class NS_capital_bonds_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of NS_capital_bonds"
    definition_period = YEAR


class NS_capital_bonds_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from NS_capital_bonds"
    definition_period = YEAR


class NS_capital_bonds_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_capital_bonds income is pre-tax"
    definition_period = YEAR


class NS_capital_bonds_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_capital_bonds is a joint account"
    definition_period = YEAR


class ILNSC_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of ILNSC"
    definition_period = YEAR


class ILNSC_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from ILNSC"
    definition_period = YEAR


class ILNSC_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether ILNSC income is pre-tax"
    definition_period = YEAR


class ILNSC_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether ILNSC is a joint account"
    definition_period = YEAR


class FINSC_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of FINSC"
    definition_period = YEAR


class FINSC_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from FINSC"
    definition_period = YEAR


class FINSC_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether FINSC income is pre-tax"
    definition_period = YEAR


class FINSC_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether FINSC is a joint account"
    definition_period = YEAR


class PGB_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of PGB"
    definition_period = YEAR


class PGB_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from PGB"
    definition_period = YEAR


class PGB_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether PGB income is pre-tax"
    definition_period = YEAR


class PGB_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether PGB is a joint account"
    definition_period = YEAR


class SAYE_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of SAYE"
    definition_period = YEAR


class SAYE_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from SAYE"
    definition_period = YEAR


class SAYE_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether SAYE income is pre-tax"
    definition_period = YEAR


class SAYE_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether SAYE is a joint account"
    definition_period = YEAR


class premium_bonds_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of premium_bonds"
    definition_period = YEAR


class premium_bonds_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from premium_bonds"
    definition_period = YEAR


class premium_bonds_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether premium_bonds income is pre-tax"
    definition_period = YEAR


class premium_bonds_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether premium_bonds is a joint account"
    definition_period = YEAR


class NS_income_bonds_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of NS_income_bonds"
    definition_period = YEAR


class NS_income_bonds_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from NS_income_bonds"
    definition_period = YEAR


class NS_income_bonds_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_income_bonds income is pre-tax"
    definition_period = YEAR


class NS_income_bonds_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_income_bonds is a joint account"
    definition_period = YEAR


class NS_deposit_bonds_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of NS_deposit_bonds"
    definition_period = YEAR


class NS_deposit_bonds_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from NS_deposit_bonds"
    definition_period = YEAR


class NS_deposit_bonds_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_deposit_bonds income is pre-tax"
    definition_period = YEAR


class NS_deposit_bonds_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether NS_deposit_bonds is a joint account"
    definition_period = YEAR


class first_option_bonds_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of first_option_bonds"
    definition_period = YEAR


class first_option_bonds_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from first_option_bonds"
    definition_period = YEAR


class first_option_bonds_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether first_option_bonds income is pre-tax"
    definition_period = YEAR


class first_option_bonds_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether first_option_bonds is a joint account"
    definition_period = YEAR


class yearly_plan_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of yearly_plan"
    definition_period = YEAR


class yearly_plan_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from yearly_plan"
    definition_period = YEAR


class yearly_plan_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether yearly_plan income is pre-tax"
    definition_period = YEAR


class yearly_plan_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether yearly_plan is a joint account"
    definition_period = YEAR


class ISA_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of ISA"
    definition_period = YEAR


class ISA_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from ISA"
    definition_period = YEAR


class ISA_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether ISA income is pre-tax"
    definition_period = YEAR


class ISA_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether ISA is a joint account"
    definition_period = YEAR


class profit_sharing_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of profit_sharing"
    definition_period = YEAR


class profit_sharing_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from profit_sharing"
    definition_period = YEAR


class profit_sharing_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether profit_sharing income is pre-tax"
    definition_period = YEAR


class profit_sharing_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether profit_sharing is a joint account"
    definition_period = YEAR


class CSOP_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of CSOP"
    definition_period = YEAR


class CSOP_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from CSOP"
    definition_period = YEAR


class CSOP_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether CSOP income is pre-tax"
    definition_period = YEAR


class CSOP_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether CSOP is a joint account"
    definition_period = YEAR


class member_of_share_club_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of member_of_share_club"
    definition_period = YEAR


class member_of_share_club_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from member_of_share_club"
    definition_period = YEAR


class member_of_share_club_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether member_of_share_club income is pre-tax"
    definition_period = YEAR


class member_of_share_club_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether member_of_share_club is a joint account"
    definition_period = YEAR


class guaranteed_income_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of guaranteed_income"
    definition_period = YEAR


class guaranteed_income_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from guaranteed_income"
    definition_period = YEAR


class guaranteed_income_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether guaranteed_income income is pre-tax"
    definition_period = YEAR


class guaranteed_income_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether guaranteed_income is a joint account"
    definition_period = YEAR


class GEB_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of GEB"
    definition_period = YEAR


class GEB_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from GEB"
    definition_period = YEAR


class GEB_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether GEB income is pre-tax"
    definition_period = YEAR


class GEB_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether GEB is a joint account"
    definition_period = YEAR


class basic_account_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of basic_account"
    definition_period = YEAR


class basic_account_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from basic_account"
    definition_period = YEAR


class basic_account_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether basic_account income is pre-tax"
    definition_period = YEAR


class basic_account_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether basic_account is a joint account"
    definition_period = YEAR


class credit_unions_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of credit_unions"
    definition_period = YEAR


class credit_unions_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from credit_unions"
    definition_period = YEAR


class credit_unions_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether credit_unions income is pre-tax"
    definition_period = YEAR


class credit_unions_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether credit_unions is a joint account"
    definition_period = YEAR


class EPNL_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of EPNL"
    definition_period = YEAR


class EPNL_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from EPNL"
    definition_period = YEAR


class EPNL_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether EPNL income is pre-tax"
    definition_period = YEAR


class EPNL_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether EPNL is a joint account"
    definition_period = YEAR


class post_office_card_account_value(Variable):
    value_type = float
    entity = Person
    label = u"Value of post_office_card_account"
    definition_period = YEAR


class post_office_card_account_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from post_office_card_account"
    definition_period = YEAR


class post_office_card_account_pre_tax(Variable):
    value_type = bool
    entity = Person
    label = u"Whether post_office_card_account income is pre-tax"
    definition_period = YEAR


class post_office_card_account_is_joint(Variable):
    value_type = bool
    entity = Person
    label = u"Whether post_office_card_account is a joint account"
    definition_period = YEAR
