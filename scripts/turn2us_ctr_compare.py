#!/usr/bin/env python3

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

import requests


BASE_URL = "https://benefits-calculator-api.turn2us.org.uk"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)
STATE = {
    "partner": None,
    "referral": None,
    "subCategory": None,
    "test": None,
    "pipSessionId": None,
    "isMobile": False,
    "browserVersion": "136.0.0.0",
    "browserName": "Chrome",
    "OsName": "Mac OS",
    "browserId": "policyengine_turn2us_probe",
}


@dataclass(frozen=True)
class Scenario:
    description: str
    build_steps: Callable[[dict[str, Any]], list[dict[str, Any]]]


def build_single_jsa_steps(postcode_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ClientMemberHousehold": "Yes",
            "ClientPartnerStudent": "No",
            "ClientPartnerPrison": "No",
            "ClientPartnerHospital": "No",
        },
        {},
        {
            "ClientPostcode": postcode_payload,
            "ClientLiveWithPartner": "No",
            "ClientDob": "01/01/1991",
        },
        {},
        {"ClientPartnerReceivingBens": "Yes"},
        {
            "ClientPartnerUcReceiving": "No",
            "ClientPartnerIrEsa": "No",
            "ClientPartnerIncomeSupport": "No",
            "ClientPartnerIbJsa": "Yes",
            "IbJsaSingleCouple": "Single",
            "ClientPartnerHousingBenefit": "No",
            "ManagedMigration": "No",
        },
        {"ClientIncomeFromBenefits": ["None of the above"]},
        {},
        {"ClientSicknessDisability": "No", "ClientRegisteredBlind": "No"},
        {},
        {"ClientCarer": "No", "ClientCarerAllow": "No", "ClientCarerSupport": "No"},
        {},
        {
            "ClientIsApprovedFosterCarer": "No",
            "ClientHasChildren": "No",
            "ClientExpectingBaby": "No",
        },
        {},
        {},
        {"ClientHousingCosts": "I own my home with a mortgage"},
        {"BetterOffCalc": "No", "ClientWorking": "Unemployed and looking for work"},
        {"ClientWarPension": "No"},
        {"ClientSpousalMaintenance": "No"},
        {},
        {"ClientPropertyCommercial": "No"},
        {"ClientCapitalEstimate": "£0 - £5000"},
    ]


def build_couple_jsa_steps(postcode_payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = build_single_jsa_steps(postcode_payload)
    steps[2] = {
        **steps[2],
        "ClientLiveWithPartner": "Yes",
        "PartnerDob": "01/01/1991",
    }
    steps[5] = {**steps[5], "IbJsaSingleCouple": "Couple"}
    # Turn2us inserts partner-only work / pension pages for couples.
    steps.extend([{}, {}, {}, {}, {}])
    return steps


def build_lone_parent_one_child_jsa_steps(
    postcode_payload: dict[str, Any]
) -> list[dict[str, Any]]:
    steps = build_single_jsa_steps(postcode_payload)
    steps[12] = {
        **steps[12],
        "ClientHasChildren": "Yes",
        "ClientDependentChildren": "1",
        "ClientExpectingBaby": "No",
    }
    steps[13] = {
        "ChildGenderOne": "Male",
        "ChildDobOne": "01/01/2021",
        "ChildDisabilityOne": "No",
    }
    return steps


def build_single_pension_credit_steps(
    postcode_payload: dict[str, Any]
) -> list[dict[str, Any]]:
    steps = build_single_jsa_steps(postcode_payload)
    steps[2] = {**steps[2], "ClientDob": "01/01/1956"}
    steps[5] = {
        "ClientPartnerUcReceiving": "No",
        "ClientPartnerIrEsa": "No",
        "ClientPartnerIncomeSupport": "No",
        "ClientPartnerIbJsa": "No",
        "ClientPartnerHousingBenefit": "No",
        "ClientPartnerPensionCredit": "Yes",
        "ClientSavingPension": "Yes",
        "ManagedMigration": "No",
    }
    steps[17] = {
        "ClientIncomeStatePension": {"weekly": "185.15", "period": "weekly"},
        "ClientStatePensionDeferred": {"weekly": "0", "period": "weekly"},
        "ClientIncomeOccupationalPension": {"weekly": "0", "period": "weekly"},
    }
    return steps


SCENARIOS = {
    "single_jsa": Scenario(
        description="Single working-age claimant on income-based JSA.",
        build_steps=build_single_jsa_steps,
    ),
    "couple_jsa": Scenario(
        description="Couple with no children on income-based JSA.",
        build_steps=build_couple_jsa_steps,
    ),
    "lone_parent_one_child_jsa": Scenario(
        description="Lone parent with one child on income-based JSA.",
        build_steps=build_lone_parent_one_child_jsa_steps,
    ),
    "single_pension_credit": Scenario(
        description="Single pension-age claimant with Pension Credit and State Pension.",
        build_steps=build_single_pension_credit_steps,
    ),
}


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://benefits-calculator.turn2us.org.uk",
            "Referer": "https://benefits-calculator.turn2us.org.uk/",
        }
    )
    return session


def resolve_postcode(session: requests.Session, postcode: str) -> dict[str, Any]:
    response = session.post(
        f"{BASE_URL}/api/data/postcode/",
        json={"postcode": postcode, "browserId": STATE["browserId"]},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("valid"):
        raise RuntimeError(f"Turn2us rejected postcode {postcode!r}: {payload}")
    return payload["value"]


def start_survey(session: requests.Session) -> dict[str, Any]:
    response = session.get(f"{BASE_URL}/api/data/survey", timeout=30)
    response.raise_for_status()
    return response.json()


def advance_survey(
    session: requests.Session, state: dict[str, Any], answers: dict[str, Any]
) -> dict[str, Any]:
    payload = {
        **answers,
        "session": state["session"],
        "page": state["pageNumber"],
        "action": 2,
        **STATE,
    }
    response = session.post(f"{BASE_URL}/api/data/survey/", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_results(session: requests.Session, survey_state: dict[str, Any]) -> dict[str, Any]:
    response = session.get(
        f"{BASE_URL}/api/data/result/?session={survey_state['session']}",
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def benefit_names(result: dict[str, Any], bucket: str) -> list[str]:
    return [
        item.get("benefitName")
        for item in result["benefits"].get(bucket, []) or []
        if item.get("benefitName")
    ]


def bucket_totals(result: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    return [
        {
            "benefit_name": item.get("benefitName"),
            "weekly_payment": item.get("weeklyPayment"),
            "monthly_payment": item.get("monthlyPayment"),
        }
        for item in result["benefits"].get(bucket, []) or []
    ]


def find_council_tax_mentions(result: dict[str, Any]) -> list[str]:
    mentions: list[str] = []
    for bucket in ("meansTested", "nonMeansTested", "universalCredit"):
        for item in result["benefits"].get(bucket, []) or []:
            benefit_name = item.get("benefitName") or ""
            if "council" in benefit_name.lower():
                mentions.append(benefit_name)
            for element in item.get("elements", []) or []:
                name = element.get("name") or ""
                if "council" in name.lower():
                    mentions.append(name)
            for deduction in item.get("deductions", []) or []:
                name = deduction.get("name") or ""
                if "council" in name.lower():
                    mentions.append(name)
    return mentions


def run_case(postcode: str, scenario_name: str) -> dict[str, Any]:
    session = build_session()
    postcode_payload = resolve_postcode(session, postcode)
    survey_state = start_survey(session)
    scenario = SCENARIOS[scenario_name]
    for answers in scenario.build_steps(postcode_payload):
        survey_state = advance_survey(session, survey_state, answers)
    for _ in range(10):
        if survey_state["pageNumber"] == 109:
            break
        survey_state = advance_survey(session, survey_state, {})
    result = fetch_results(session, survey_state)
    return {
        "scenario": scenario_name,
        "description": scenario.description,
        "postcode": postcode,
        "authority": postcode_payload["authority"],
        "authority_code": postcode_payload["authorityCode"],
        "country": postcode_payload["country"],
        "final_page_number": survey_state["pageNumber"],
        "final_page_title": survey_state["page"]["title"],
        "reached_results_page": survey_state["pageNumber"] == 109,
        "means_tested": bucket_totals(result, "meansTested"),
        "universal_credit": bucket_totals(result, "universalCredit"),
        "non_means_tested": bucket_totals(result, "nonMeansTested"),
        "council_tax_mentions": find_council_tax_mentions(result),
        "messages_with_council_tax_terms": [
            message
            for message in result.get("messages", []) or []
            if "council" in json.dumps(message).lower()
        ],
        "raw_result_path": None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("postcode", nargs="+")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[*SCENARIOS.keys(), "all"],
        default=None,
    )
    parser.add_argument("--save-raw-dir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario_names = args.scenario or ["single_jsa"]
    if "all" in scenario_names:
        scenario_names = list(SCENARIOS.keys())
    else:
        scenario_names = list(dict.fromkeys(scenario_names))
    results = []
    for scenario_name in scenario_names:
        for postcode in args.postcode:
            case = run_case(postcode, scenario_name)
            if args.save_raw_dir is not None:
                from pathlib import Path

                raw_dir = Path(args.save_raw_dir)
                raw_dir.mkdir(parents=True, exist_ok=True)
                out_path = raw_dir / (
                    f"{scenario_name}_{postcode.replace(' ', '_')}.json"
                )
                out_path.write_text(json.dumps(case, indent=2))
                case["raw_result_path"] = str(out_path)
            results.append(case)
    json.dump(results, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
