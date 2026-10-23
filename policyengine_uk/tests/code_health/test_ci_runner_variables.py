"""Which runner each CI job uses, and what the runner variables can move.

The test jobs and the check jobs a merge queue group or release waits on
run on today's GitHub-hosted labels unless a repository variable names
another runner (test-suite.yaml explains the variables). These tests hold
the workflows to that:

1. Each covered job's ``runs-on`` is the one runner expression, built from
   its variable and today's label, so an unset variable keeps the label.
2. Every other job keeps a literal GitHub-hosted label. The jobs that make
   the version commit, build and publish the release, check fix evidence
   on pull_request_target, aggregate impact (household-level detail stays
   on the runner) and deploy the docs never move.
3. The expression picks the variable's runner exactly when the variable is
   set and CI_RUNNER_EVENTS is empty or lists the run's event, matched as a
   whole name: "pull_request" never matches "pull_request_target".
4. Every job that can move has a GITHUB_TOKEN that can only read: the
   organisation's default token can write, and a moved job takes its token
   to the other runner. ``id-token: write`` stays allowed: it only lets a
   job ask GitHub for an OIDC token, which the tests use for GCP.
"""

from itertools import product
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[3] / ".github" / "workflows"
if not WORKFLOWS.is_dir():
    # The release workflow tests the installed wheel, which has no .github.
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )

ARM, X64 = "ubuntu-24.04-arm", "ubuntu-latest"

# (workflow, job) -> (variable, today's label)
COVERED = {
    ("test-suite.yaml", "YAML"): ("CI_RUNNER_ARM", ARM),
    ("test-suite.yaml", "Python"): ("CI_RUNNER_ARM", ARM),
    ("test-suite.yaml", "Result"): ("CI_RUNNER_ARM", ARM),
    ("pr_code_changes.yaml", "Changes"): ("CI_RUNNER_ARM", ARM),
    ("pr_code_changes.yaml", "Python-Compat"): ("CI_RUNNER_X64", X64),
    ("pr_code_changes.yaml", "Lint"): ("CI_RUNNER_X64", X64),
    ("pr_code_changes.yaml", "Docs"): ("CI_RUNNER_X64", X64),
    ("code_changes.yaml", "Tested"): ("CI_RUNNER_ARM", ARM),
    ("code_changes.yaml", "Lint"): ("CI_RUNNER_X64", X64),
    ("versioning.yaml", "Lint"): ("CI_RUNNER_X64", X64),
    ("versioning.yaml", "Compat"): ("CI_RUNNER_X64", X64),
    ("versioning.yaml", "Sdist"): ("CI_RUNNER_X64", X64),
}

NEVER_MOVED = {
    ("versioning.yaml", "Versioning"),
    ("versioning.yaml", "Build"),
    ("versioning.yaml", "Publish"),
    ("pr_fix_evidence.yaml", "Fix-evidence"),
    ("aggregate-impact.yaml", "report"),
    ("deploy.yml", "deploy"),
}


def runner_expression(variable, label):
    return (
        f"${{{{ vars.{variable} != '' && (vars.CI_RUNNER_EVENTS == '' || "
        "contains(format(',{0},', vars.CI_RUNNER_EVENTS), format(',{0},', github.event_name))) "
        f"&& vars.{variable} || '{label}' }}}}"
    )


def documents():
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        yield path.name, yaml.safe_load(path.read_text(encoding="utf-8"))


def jobs():
    for name, document in documents():
        for job_name, job in document["jobs"].items():
            if "runs-on" in job:
                yield (name, job_name), job["runs-on"]


# Invariant 1.


def test_covered_jobs_use_the_runner_expression():
    found = dict(jobs())
    for key, (variable, label) in COVERED.items():
        assert found[key] == runner_expression(variable, label), key


# Invariant 2.


def test_every_other_job_keeps_a_github_hosted_label():
    found = dict(jobs())
    assert NEVER_MOVED <= set(found)
    for key, runs_on in found.items():
        if key in COVERED:
            continue
        assert runs_on in (ARM, X64), (key, runs_on)


# Invariant 3: the expression's rule, as GitHub evaluates it. "a && b || c"
# gives b when a and b are non-empty, else c; an unset variable is "".


def chosen_runner(variable_value, events_value, event, label):
    if variable_value != "" and (
        events_value == "" or f",{event}," in f",{events_value},"
    ):
        return variable_value
    return label


EVENTS = [
    "pull_request",
    "pull_request_target",
    "merge_group",
    "push",
    "workflow_dispatch",
    "schedule",
]
EVENT_LISTS = [
    "",
    "merge_group",
    "merge_group,push",
    "pull_request",
    "pull_request_target",
    "push,workflow_dispatch,merge_group",
]


@pytest.mark.parametrize(
    "variable_value,events_value,event",
    list(product(["", "pe-arm64-4core"], EVENT_LISTS, EVENTS)),
)
def test_the_variable_applies_only_to_the_listed_events(
    variable_value, events_value, event
):
    chosen = chosen_runner(variable_value, events_value, event, ARM)
    listed = events_value == "" or event in events_value.split(",")
    if variable_value and listed:
        assert chosen == variable_value
    else:
        assert chosen == ARM


# Invariant 4.


def test_jobs_that_can_move_hold_a_read_only_token():
    workflows = dict(documents())
    for workflow, job_name in COVERED:
        document = workflows[workflow]
        job = document["jobs"][job_name]
        # A job's own permissions replace the workflow's; with neither, the
        # job gets the organisation's default token, which can write.
        permissions = job.get("permissions", document.get("permissions"))
        assert isinstance(permissions, dict), (workflow, job_name)
        for scope, level in permissions.items():
            assert level in ("read", "none") or scope == "id-token", (
                workflow,
                job_name,
                scope,
                level,
            )
