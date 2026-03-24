#!/usr/bin/env python3

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Callable

from policyengine_uk import Simulation


@dataclass(frozen=True)
class CouncilConfig:
    label: str
    local_authority: str
    council_tax_band: str
    council_tax: float


@dataclass(frozen=True)
class Scenario:
    description: str
    build_situation: Callable[[CouncilConfig], dict]


SINGLE_JSA_WEEKLY = 92.05
COUPLE_JSA_WEEKLY = 144.65
STATE_PENSION_WEEKLY = 185.15


COUNCILS = {
    "east_hertfordshire": CouncilConfig(
        label="East Hertfordshire",
        local_authority="EAST_HERTFORDSHIRE",
        council_tax_band="D",
        council_tax=1800.0,
    ),
    "warrington": CouncilConfig(
        label="Warrington",
        local_authority="WARRINGTON",
        council_tax_band="C",
        council_tax=126.74 * 12,
    ),
    "dudley": CouncilConfig(
        label="Dudley",
        local_authority="DUDLEY",
        council_tax_band="C",
        council_tax=113.25 * 12,
    ),
    "stroud": CouncilConfig(
        label="Stroud",
        local_authority="STROUD",
        council_tax_band="D",
        council_tax=148.09 * 12,
    ),
}


def base_benunit(
    *,
    members: list[str],
    eldest_adult_age: int,
    is_single_person: bool,
    is_couple: bool,
    is_lone_parent: bool,
) -> dict:
    return {
        "members": members,
        "claims_all_entitled_benefits": {2025: False},
        "would_claim_uc": {2025: False},
        "is_single_person": {2025: is_single_person},
        "is_couple": {2025: is_couple},
        "is_lone_parent": {2025: is_lone_parent},
        "eldest_adult_age": {2025: eldest_adult_age},
        "benefits_premiums": {2025: 0},
    }


def base_household(council: CouncilConfig, members: list[str]) -> dict:
    return {
        "members": members,
        "country": {2025: "ENGLAND"},
        "local_authority": {2025: council.local_authority},
        "council_tax_band": {2025: council.council_tax_band},
        "council_tax": {2025: council.council_tax},
        "savings": {2025: 0},
    }


def build_single_jsa(council: CouncilConfig) -> dict:
    return {
        "people": {
            "claimant": {
                "age": {2025: 35},
                "jsa_income_reported": {2025: SINGLE_JSA_WEEKLY * 52},
                "council_tax_benefit_reported": {2025: 1},
            }
        },
        "benunits": {
            "benunit": base_benunit(
                members=["claimant"],
                eldest_adult_age=35,
                is_single_person=True,
                is_couple=False,
                is_lone_parent=False,
            )
        },
        "households": {
            "household": base_household(council, ["claimant"]),
        },
    }


def build_couple_jsa(council: CouncilConfig) -> dict:
    return {
        "people": {
            "claimant": {
                "age": {2025: 35},
                "jsa_income_reported": {2025: COUPLE_JSA_WEEKLY * 52},
                "council_tax_benefit_reported": {2025: 1},
            },
            "partner": {
                "age": {2025: 35},
            },
        },
        "benunits": {
            "benunit": base_benunit(
                members=["claimant", "partner"],
                eldest_adult_age=35,
                is_single_person=False,
                is_couple=True,
                is_lone_parent=False,
            )
        },
        "households": {
            "household": base_household(council, ["claimant", "partner"]),
        },
    }


def build_lone_parent_one_child_jsa(council: CouncilConfig) -> dict:
    return {
        "people": {
            "claimant": {
                "age": {2025: 35},
                "jsa_income_reported": {2025: SINGLE_JSA_WEEKLY * 52},
                "council_tax_benefit_reported": {2025: 1},
            },
            "child": {
                "age": {2025: 5},
            },
        },
        "benunits": {
            "benunit": base_benunit(
                members=["claimant", "child"],
                eldest_adult_age=35,
                is_single_person=False,
                is_couple=False,
                is_lone_parent=True,
            )
        },
        "households": {
            "household": base_household(council, ["claimant", "child"]),
        },
    }


def build_single_pension_credit(council: CouncilConfig) -> dict:
    return {
        "people": {
            "claimant": {
                "age": {2025: 70},
                "state_pension": {2025: STATE_PENSION_WEEKLY * 52},
                "council_tax_benefit_reported": {2025: 1},
            }
        },
        "benunits": {
            "benunit": {
                **base_benunit(
                    members=["claimant"],
                    eldest_adult_age=70,
                    is_single_person=True,
                    is_couple=False,
                    is_lone_parent=False,
                ),
                "would_claim_pc": {2025: True},
            }
        },
        "households": {
            "household": base_household(council, ["claimant"]),
        },
    }


SCENARIOS = {
    "single_jsa": Scenario(
        description="Single working-age claimant on income-based JSA.",
        build_situation=build_single_jsa,
    ),
    "couple_jsa": Scenario(
        description="Couple with no children on income-based JSA.",
        build_situation=build_couple_jsa,
    ),
    "lone_parent_one_child_jsa": Scenario(
        description="Lone parent with one child on income-based JSA.",
        build_situation=build_lone_parent_one_child_jsa,
    ),
    "single_pension_credit": Scenario(
        description="Single pension-age claimant with State Pension and Pension Credit.",
        build_situation=build_single_pension_credit,
    ),
}


def run_case(council_name: str, scenario_name: str) -> dict:
    council = COUNCILS[council_name]
    scenario = SCENARIOS[scenario_name]
    sim = Simulation(situation=scenario.build_situation(council))
    period = 2025
    return {
        "council": council_name,
        "council_label": council.label,
        "scenario": scenario_name,
        "description": scenario.description,
        "council_tax_band": council.council_tax_band,
        "council_tax": council.council_tax,
        "council_tax_reduction": float(sim.calculate("council_tax_reduction", period)[0]),
        "council_tax_less_benefit": float(
            sim.calculate("council_tax_less_benefit", period)[0]
        ),
        "child_benefit": float(sim.calculate("child_benefit", period)[0]),
        "pension_credit": float(sim.calculate("pension_credit", period)[0]),
        "state_pension": float(sim.calculate("state_pension", period)[0]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[*SCENARIOS.keys(), "all"],
        default=None,
    )
    parser.add_argument(
        "--council",
        action="append",
        choices=[*COUNCILS.keys(), "all"],
        default=None,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario_names = args.scenario or ["single_jsa"]
    if "all" in scenario_names:
        scenario_names = list(SCENARIOS.keys())
    else:
        scenario_names = list(dict.fromkeys(scenario_names))

    council_names = args.council or ["all"]
    if "all" in council_names:
        council_names = list(COUNCILS.keys())
    else:
        council_names = list(dict.fromkeys(council_names))

    results = []
    for scenario_name in scenario_names:
        for council_name in council_names:
            results.append(run_case(council_name, scenario_name))

    json.dump(results, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
