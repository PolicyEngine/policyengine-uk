from policyengine_uk.model_api import *


class esa_income_appointee_saving(Variable):
    value_type = bool
    entity = Person
    label = "Income-related ESA award saved from abolition for an appointee"
    documentation = (
        "Whether the old style income-related ESA award on this person's "
        "report is saved from the abolition of income-related ESA, so it stays "
        "payable after 1 July 2026 (1 October 2026 in Northern Ireland). SI "
        "2025/1148 art. 3A(2) saves an award where, immediately before that "
        "date, someone is appointed under reg 57 of the Claims and Payments "
        "Regulations 2013 to act for a claimant who is unable to act, or where "
        "the Secretary of State decided in the six months ending on that date "
        "that such an appointment was likely to be needed. SR 2025/176 art. "
        "3A(2) does the same in Northern Ireland, with the Department and reg "
        "52 of the Northern Ireland Claims and Payments Regulations 2016. A "
        "couple's award is one award: a saving for either member who reports "
        "it saves the whole claim (esa_income_payable_share), and a saving for "
        "a member who reports nothing saves nothing. A saved claim prompts no "
        "Universal Credit claim and does not move the family "
        "(esa_income_abolition_reached, legacy_benefits_closed), but a "
        "Universal Credit claim, or another legacy benefit's closure, still "
        "ends it (art. 3A(3); esa_income_report_closed). DWP identified "
        "around 500 claimants who need a personal or corporate acting body "
        "and exempted them from the June 2026 closure (LA Welfare Direct "
        "6/2026, para 53). No "
        "dataset identifies appointees, so this defaults to false and the "
        "saving is off in dataset runs."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
    )
