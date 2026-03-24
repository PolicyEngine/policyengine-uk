#!/usr/bin/env python3

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Scenario:
    description: str
    household_overrides: Optional[Dict[str, str]]
    age_overrides: Dict[str, str]
    benefits_overrides: Dict[str, str]
    partner_age_overrides: Optional[Dict[str, str]] = None
    child_overrides: Optional[Sequence[Dict[str, str]]] = None
    disability_overrides: Optional[Dict[str, str]] = None
    net_income_overrides: Optional[Dict[str, str]] = None
    housing_costs_overrides: Optional[Dict[str, str]] = None


SCENARIOS = {
    "single_jsa": Scenario(
        description="Single working-age claimant on income-based JSA.",
        household_overrides=None,
        age_overrides={
            "Age": "35",
            "Gender": "Male",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "NotClaimed",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        benefits_overrides={
            "ReceiveUniversalCredit": "False",
            "ReceiveTransitionalElement": "False",
            "IncomeBasedBenefit": "jobseekerallowanceincomebased",
            "ReceivedManagedMigrationNotice": "False",
            "ClientReceivesOtherBenefits": "False",
        },
        net_income_overrides={
            "IsClientIncomeNonStatePensions": "False",
            "IsFosteringAllowanceOption": "False",
            "IncomeFromSavingsChk": "False",
            "IsIncomeFromMaintenancePaymentsOption": "False",
            "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
            "OwnOtherProperty": "False",
            "IsOtherSourcesIncome": "False",
        },
    ),
    "single_jsa_pip_standard": Scenario(
        description="Single working-age claimant on income-based JSA with standard daily living PIP.",
        household_overrides=None,
        age_overrides={
            "Age": "35",
            "Gender": "Male",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "CurrentlyClaiming",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        disability_overrides={
            "PersonalIndependencePaymentDailyLiving.SelectedOption": "2",
            "PersonalIndependencePaymentDailyLiving.Value": "73.9",
            "PersonalIndependencePaymentDailyLiving.PaymentPeriod": "2",
        },
        benefits_overrides={
            "ReceiveUniversalCredit": "False",
            "ReceiveTransitionalElement": "False",
            "IncomeBasedBenefit": "jobseekerallowanceincomebased",
            "ReceivedManagedMigrationNotice": "False",
            "ClientReceivesOtherBenefits": "False",
        },
        net_income_overrides={
            "IsClientIncomeNonStatePensions": "False",
            "IsFosteringAllowanceOption": "False",
            "IncomeFromSavingsChk": "False",
            "IsIncomeFromMaintenancePaymentsOption": "False",
            "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
            "OwnOtherProperty": "False",
            "IsOtherSourcesIncome": "False",
        },
    ),
    "single_pension_credit": Scenario(
        description="Single pension-age claimant with Pension Credit and State Pension.",
        household_overrides=None,
        age_overrides={
            "Age": "70",
            "DOB_Day": "1",
            "DOB_Month": "1",
            "DOB_Year": "1956",
            "Gender": "Male",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "NotClaimed",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        benefits_overrides={
            "HasPensionCredit": "True",
            "ClientRetirementPension.SelectedOption": "1",
            "ClientRetirementPension.Value": "185.15",
            "ClientRetirementPension.PaymentPeriod": "2",
            "ClientReceivesOtherBenefits": "False",
        },
        net_income_overrides={
            "IsClientIncomeNonStatePensions": "False",
            "IsFosteringAllowanceOption": "False",
            "IncomeFromSavingsChk": "False",
            "IsIncomeFromMaintenancePaymentsOption": "False",
            "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
            "OwnOtherProperty": "False",
            "IsOtherSourcesIncome": "False",
        },
    ),
    "couple_jsa": Scenario(
        description="Couple with no children on income-based JSA.",
        household_overrides={
            "HasPartner": "True",
        },
        age_overrides={
            "Age": "35",
            "Gender": "Male",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "NotClaimed",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        partner_age_overrides={
            "Age": "35",
            "Gender": "Female",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "NotClaimed",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        benefits_overrides={
            "ReceiveUniversalCredit": "False",
            "ReceiveTransitionalElement": "False",
            "IncomeBasedBenefit": "jobseekerallowanceincomebased",
            "ReceivedManagedMigrationNotice": "False",
            "ClientReceivesOtherBenefits": "False",
        },
        net_income_overrides={
            "IsClientIncomeNonStatePensions": "False",
            "IsFosteringAllowanceOption": "False",
            "IncomeFromSavingsChk": "False",
            "IsIncomeFromMaintenancePaymentsOption": "False",
            "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
            "OwnOtherProperty": "False",
            "IsOtherSourcesIncome": "False",
        },
    ),
    "lone_parent_one_child_jsa": Scenario(
        description="Lone parent with one child on income-based JSA.",
        household_overrides={
            "HouseholdChildrenNumber": "1",
        },
        age_overrides={
            "Age": "35",
            "Gender": "Male",
            "ClientWorkStatus": "NotEmployed",
            "WeekWorkHoursAmount": "0",
            "WorkStatus": "False",
            "ClientDisbens": "NotClaimed",
            "ClientDisabledNotClaiming": "False",
            "ClientCareForDisabled": "False",
        },
        child_overrides=[
            {
                "Age": "5",
                "DOB_Day": "1",
                "DOB_Month": "1",
                "DOB_Year": "2021",
                "PayForChildcare": "False",
                "ChildcarePeriod": "2",
                "ChildcareAmount": "0",
                "IsDisabledPerson": "False",
                "IsDisabledNotClaiming": "False",
            }
        ],
        benefits_overrides={
            "ReceiveUniversalCredit": "False",
            "ReceiveTransitionalElement": "False",
            "IncomeBasedBenefit": "jobseekerallowanceincomebased",
            "ReceivedManagedMigrationNotice": "False",
            "ClientReceivesOtherBenefits": "False",
        },
        net_income_overrides={
            "IsClientIncomeNonStatePensions": "False",
            "IsFosteringAllowanceOption": "False",
            "IncomeFromSavingsChk": "False",
            "IsIncomeFromMaintenancePaymentsOption": "False",
            "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
            "OwnOtherProperty": "False",
            "IsOtherSourcesIncome": "False",
        },
    ),
}


HOUSEHOLD_TEMPLATE = {
    "CompanyName": "entitledto",
    "HasSEISS": "False",
    "HideNonDeps": "False",
    "SiteId": "4",
    "CalcYears": "22",
    "HasPartner": "False",
    "HouseholdChildrenNumber": "0",
    "AnyoneElseLivesInYourHome": "No",
    "ImmigrationControl": "True",
    "ClientImmigrationStatus": "BritishOrIrish",
    "CoronaVirusStatus": "None",
    "ResCare": "False",
    "VehiclesModel.DoYouOwnAVehicle": "False",
    "VehiclesModel.NumberOfVehicles": "0",
    "NavigationControls.SaveButtonIsPressed": "False",
    "NavigationControls.ShowSaveButton": "True",
    "NavigationControls.ShowNextButton": "True",
}


EMPTY_NET_INCOME = {
    "IsClientIncomeNonStatePensions": "False",
    "IsFosteringAllowanceOption": "False",
    "IncomeFromSavingsChk": "False",
    "IsIncomeFromMaintenancePaymentsOption": "False",
    "IsIncomeFromVoluntaryCharitablePaymentsOption": "False",
    "OwnOtherProperty": "False",
    "IsOtherSourcesIncome": "False",
}


def load_session(storage_state_path: Path) -> requests.Session:
    state = json.loads(storage_state_path.read_text())
    session = requests.Session()
    for cookie in state.get("cookies", []):
        domain = cookie.get("domain", "")
        if "entitledto.co.uk" not in domain:
            continue
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=domain,
            path=cookie.get("path", "/"),
        )
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def find_resume_cid(session: requests.Session) -> Optional[str]:
    for cookie in session.cookies:
        match = re.match(
            r"f_/benefits-calculator/Intro/Home\?cid([0-9a-f-]{36})",
            cookie.name,
        )
        if match:
            return match.group(1)
    return None


def extract_primary_form(html: str, current_url: str) -> tuple[str, Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    candidate = None
    for form in soup.find_all("form"):
        if "/benefits-calculator/" in (form.get("action") or ""):
            candidate = form
            break
    if candidate is None:
        raise RuntimeError(f"No entitledto calculator form found at {current_url}")

    action = urljoin(current_url, candidate.get("action", current_url))
    payload: Dict[str, str] = {}
    radio_groups = set()

    for element in candidate.find_all(["input", "select", "textarea"]):
        name = element.get("name")
        if not name:
            continue
        tag = element.name
        element_type = (element.get("type") or "").lower()

        if tag == "select":
            selected = element.find("option", selected=True) or element.find("option")
            payload[name] = selected.get("value", "") if selected else ""
            continue

        if tag == "textarea":
            payload[name] = element.text or ""
            continue

        if element_type in {"submit", "button", "image", "file", "reset"}:
            continue

        value = element.get("value", "")
        data_value = element.get("data-value")
        if (
            data_value is not None
            and element_type == "hidden"
            and (
                value.startswith("System.String")
                or value.startswith("System.Collections.Generic")
            )
        ):
            value = data_value

        if element_type == "radio":
            if name in radio_groups:
                continue
            checked = candidate.find("input", attrs={"name": name, "checked": True})
            if checked is not None:
                payload[name] = checked.get("value", "")
            radio_groups.add(name)
            continue

        if element_type == "checkbox":
            if element.has_attr("checked"):
                payload[name] = value or "on"
            continue

        payload[name] = value

    return action, payload


def follow_post(
    session: requests.Session, action: str, payload: Dict[str, str]
) -> requests.Response:
    response = session.post(action, data=payload, allow_redirects=False, timeout=30)
    if response.is_redirect or response.is_permanent_redirect:
        location = response.headers["location"]
        return session.get(urljoin(action, location), timeout=30)
    return response


def page_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.title.get_text(strip=True) if soup.title else ""


def bootstrap_calculation(
    session: requests.Session,
    postcode: str,
    housing_status: str,
    household_overrides: Optional[Dict[str, str]] = None,
) -> requests.Response:
    response = None
    action = None
    payload = None
    resume_cid = find_resume_cid(session)
    if resume_cid is not None:
        response = session.get(
            f"https://www.entitledto.co.uk/benefits-calculator/Intro/Home?cid={resume_cid}",
            timeout=30,
        )
    else:
        response = session.get(
            "https://www.entitledto.co.uk/benefits-calculator/",
            timeout=30,
        )
    for _ in range(5):
        action, payload = extract_primary_form(response.text, response.url)
        if "CalcIdent" in payload:
            break
        response = follow_post(session, action, payload)
    if response is None or action is None or payload is None or "CalcIdent" not in payload:
        raise RuntimeError(
            "entitledto did not return the calculator start page with a CalcIdent"
        )
    payload.update(
        {
            "NationalHousingStatus": housing_status,
            "Postcode": postcode,
        }
    )
    response = follow_post(session, action, payload)
    household_payload = dict(HOUSEHOLD_TEMPLATE)
    action, household_defaults = extract_primary_form(response.text, response.url)
    household_payload["CalcIdent"] = household_defaults["CalcIdent"]
    household_payload["StartTime"] = household_defaults["StartTime"]
    household_payload.update(household_overrides or {})
    return follow_post(session, action, household_payload)


def post_form_overrides(
    session: requests.Session,
    response: requests.Response,
    overrides: Optional[Dict[str, str]] = None,
) -> requests.Response:
    action, payload = extract_primary_form(response.text, response.url)
    payload.update(overrides or {})
    return follow_post(session, action, payload)


def post_until(
    session: requests.Session,
    response: requests.Response,
    overrides: Optional[Dict[str, str]],
    predicate: Callable[[requests.Response], bool],
    attempts: int = 3,
) -> requests.Response:
    for _ in range(attempts):
        response = post_form_overrides(session, response, overrides)
        if predicate(response):
            return response
    return response


def require_page(response: requests.Response, fragment: str) -> None:
    if fragment not in response.url:
        raise RuntimeError(
            f"Expected entitledto page containing {fragment!r}, got {response.url!r}"
        )


def normalize_text(html: str) -> str:
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ", strip=True).split())


def extract_money(pattern: str, text: str) -> Optional[str]:
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1).replace(" ", "")


def parse_results(html: str) -> Dict[str, Optional[str]]:
    text = normalize_text(html)
    payment_period_match = re.search(
        r"Council Tax Support £\s*([0-9][0-9,\.\s]*)\s*/\s*(weekly|4 weeks|monthly|yearly)",
        text,
        re.IGNORECASE,
    )
    bill_match = re.search(
        r"full Council Tax bill of £\s*([0-9][0-9,\.\s]*)\s*per\s*(week|4 weeks|month|year)"
        r"\s*will be reduced to £\s*([0-9][0-9,\.\s]*)\s*per\s*(week|4 weeks|month|year)",
        text,
        re.IGNORECASE,
    )
    total_match = re.search(
        r"Total benefits entitlement.*?£\s*([0-9][0-9,\.\s]*)\s*/\s*(weekly|4 weeks|monthly|yearly)",
        text,
        re.IGNORECASE,
    )
    return {
        "council_tax_support": payment_period_match.group(1).replace(" ", "")
        if payment_period_match
        else None,
        "council_tax_support_period": payment_period_match.group(2)
        if payment_period_match
        else None,
        "council_tax_bill_before": bill_match.group(1).replace(" ", "")
        if bill_match
        else None,
        "council_tax_bill_before_period": bill_match.group(2) if bill_match else None,
        "council_tax_bill_after": bill_match.group(3).replace(" ", "")
        if bill_match
        else None,
        "council_tax_bill_after_period": bill_match.group(4) if bill_match else None,
        "total_benefits": total_match.group(1).replace(" ", "") if total_match else None,
        "total_benefits_period": total_match.group(2) if total_match else None,
    }


def run_scenario(
    session: requests.Session,
    scenario_name: str,
    postcode: str,
    housing_status: str,
    council_tax_band: str,
    council_tax: str,
    use_band_amount: bool,
    save_html_dir: Optional[Path],
) -> Dict[str, Optional[str]]:
    scenario = SCENARIOS[scenario_name]
    response = bootstrap_calculation(
        session,
        postcode,
        housing_status,
        household_overrides=scenario.household_overrides,
    )
    require_page(response, "/AgeDisabilityStatus")
    if scenario.partner_age_overrides is not None:
        response = post_until(
            session,
            response,
            scenario.age_overrides,
            lambda resp: "client=Partner" in resp.url,
        )
    elif scenario.child_overrides is not None:
        response = post_until(
            session,
            response,
            scenario.age_overrides,
            lambda resp: "/Children" in resp.url,
        )
    else:
        response = post_until(
            session,
            response,
            scenario.age_overrides,
            lambda resp: (
                "/BenefitsYouCurrentlyReceive" in resp.url
                or "/DisabilityBenefits" in resp.url
            ),
        )

    if scenario.partner_age_overrides is not None:
        require_page(response, "/AgeDisabilityStatus")
        response = post_until(
            session,
            response,
            scenario.partner_age_overrides,
            lambda resp: "/BenefitsYouCurrentlyReceive" in resp.url,
        )

    if scenario.child_overrides is not None:
        for child_overrides in scenario.child_overrides:
            require_page(response, "/Children")
            response = post_until(
                session,
                response,
                child_overrides,
                lambda resp: "/BenefitsYouCurrentlyReceive" in resp.url
                or "/Children" in resp.url,
            )

    if "/DisabilityBenefits" in response.url:
        if scenario.disability_overrides is None:
            raise RuntimeError(
                f"{scenario_name} reached DisabilityBenefits without a disability payload"
            )
        response = post_until(
            session,
            response,
            scenario.disability_overrides,
            lambda resp: "/BenefitsYouCurrentlyReceive" in resp.url,
        )

    require_page(response, "/BenefitsYouCurrentlyReceive")
    response = post_until(
        session,
        response,
        scenario.benefits_overrides,
        lambda resp: "/NetIncome" in resp.url,
    )
    require_page(response, "/NetIncome")
    response = post_form_overrides(
        session,
        response,
        {**EMPTY_NET_INCOME, **(scenario.net_income_overrides or {})},
    )
    require_page(response, "/HousingCosts")
    response = post_until(
        session,
        response,
        scenario.housing_costs_overrides,
        lambda resp: "/CouncilTax" in resp.url,
    )
    require_page(response, "/CouncilTax")
    response = post_form_overrides(
        session,
        response,
        {
            "CouncilTaxBand": council_tax_band,
            "EligibleDisabilityReduction": "False",
            "DiscountsApplicable": "0",
            "AmountIsCorrect": "True" if use_band_amount else "False",
            "CouncilTax": council_tax,
            "CouncilTaxPeriod": "0",
        },
    )

    if "/Results/" not in response.url:
        raise RuntimeError(
            f"{scenario_name} did not reach entitledto results; stopped at {response.url}"
        )

    if save_html_dir is not None:
        save_html_dir.mkdir(parents=True, exist_ok=True)
        output_path = save_html_dir / f"{scenario_name}.html"
        output_path.write_text(response.text)

    result = {
        "scenario": scenario_name,
        "description": scenario.description,
        "postcode": postcode,
        "housing_status": housing_status,
        "council_tax_band": council_tax_band,
        "council_tax": council_tax,
        "results_url": response.url,
        "results_title": page_title(response.text),
    }
    result.update(parse_results(response.text))
    return result


def run_scenario_with_retries(
    storage_state_path: Path,
    scenario_name: str,
    postcode: str,
    housing_status: str,
    council_tax_band: str,
    council_tax: str,
    use_band_amount: bool,
    save_html_dir: Optional[Path],
    attempts: int,
) -> Dict[str, Optional[str]]:
    last_error: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return run_scenario(
                session=load_session(storage_state_path),
                scenario_name=scenario_name,
                postcode=postcode,
                housing_status=housing_status,
                council_tax_band=council_tax_band,
                council_tax=council_tax,
                use_band_amount=use_band_amount,
                save_html_dir=save_html_dir,
            )
        except Exception as error:
            last_error = error
            if attempt < attempts:
                time.sleep(1)
    assert last_error is not None
    raise last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("storage_state", type=Path)
    parser.add_argument("--postcode", required=True)
    parser.add_argument("--housing-status", default="MortgageOrOwned")
    parser.add_argument("--band", default="D")
    parser.add_argument("--council-tax", default="1800")
    parser.add_argument(
        "--use-band-amount",
        action="store_true",
        help="Use entitledto's band-derived bill instead of the provided annual bill.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[*SCENARIOS.keys(), "all"],
        default=["single_jsa"],
        help="Scenario to run. Repeatable. Use 'all' to run every built-in scenario.",
    )
    parser.add_argument("--save-html-dir", type=Path)
    parser.add_argument("--attempts", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario_names = args.scenario
    if "all" in scenario_names:
        scenario_names = list(SCENARIOS.keys())
    else:
        # Preserve order while removing accidental duplicates.
        scenario_names = list(dict.fromkeys(scenario_names))

    try:
        results = [
            run_scenario_with_retries(
                storage_state_path=args.storage_state,
                scenario_name=scenario_name,
                postcode=args.postcode,
                housing_status=args.housing_status,
                council_tax_band=args.band,
                council_tax=args.council_tax,
                use_band_amount=args.use_band_amount,
                save_html_dir=args.save_html_dir,
                attempts=args.attempts,
            )
            for scenario_name in scenario_names
        ]
    except Exception as error:
        print(
            f"error: {error}\n"
            "If entitledto returned Cloudflare again, refresh the storage state first "
            "with `playwright-cli state-save` or another browser-derived cookie export.",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
