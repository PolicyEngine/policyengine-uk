"""What the aggregate-impact job compares, and what may leave it.

Comparison base. For a pull request the head is GitHub's merge commit and
the base is that commit's first parent, so the report is exactly what
merging would change. The event's ``pull_request.base.sha`` lags the base
branch once the branch moves on, and a report against it counted main's
newer merges as the pull request's impact (#2516's took in 26 commits from
main). These tests run the workflow's own step scripts on real histories,
with the head fetched as actions/checkout fetches it at the workflow's
fetch depth, and hold the job to:

1. The base is the merge commit's first parent for every shape of history,
   so no commit of the base branch is counted as the pull request's.
2. A head that is not a merge of two commits fails the job with an error
   and sets no base.
3. No step reads ``pull_request.base.sha``, and the base checkout uses the
   base the job chose.
4. A manual dispatch compares the commits it names, as before.

No data access. A Dependabot run cannot read the certified dataset, so it
measures nothing. The comparison still runs, reports the run as skipped and
passes. (It used to fail every Dependabot pull request: the measure step
stopped before it set up the tool the comparison runs.)

Data protection. Only aggregates may leave the job. The certified dataset
is licensed survey microdata. The measurement keeps household-level detail
for the decile comparison under ``private/``; these tests fail if the
workflow could publish it, or could put the dataset where other workflows
can read it.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.measure import (
    HOUSEHOLDS_FILE,
    PRIVATE_DIRECTORY,
    read_result,
    write_result,
)

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github" / "workflows" / "aggregate-impact.yaml"

if not WORKFLOW.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )
ALLOWED_UPLOAD_PATHS = {"report"}


def steps():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


def test_only_the_aggregate_report_is_uploaded():
    uploads = [s for s in steps() if "upload-artifact" in str(s.get("uses", ""))]
    assert uploads, "the report should be uploaded"
    for step in uploads:
        paths = {p.strip() for p in str(step["with"]["path"]).splitlines() if p.strip()}
        assert paths <= ALLOWED_UPLOAD_PATHS, paths


def test_the_dataset_is_never_cached():
    for step in steps():
        assert "actions/cache" not in str(step.get("uses", "")), step.get("name")


def test_nothing_private_is_copied_into_the_report():
    text = WORKFLOW.read_text()
    copies = [
        line.strip() for line in text.splitlines() if line.strip().startswith("cp ")
    ]
    for line in copies:
        if "report/" in line:
            assert line.split()[1].endswith("result.json"), line
    assert f"{PRIVATE_DIRECTORY}/" not in "\n".join(copies)
    assert HOUSEHOLDS_FILE not in "\n".join(copies)


def test_the_job_runs_both_sides_itself():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    assert list(workflow["jobs"]) == ["report"], (
        "base and head must be measured in one job, so that household detail "
        "never has to travel between jobs as an artifact"
    )
    assert not [s for s in steps() if "download-artifact" in str(s.get("uses", ""))]


def test_household_detail_is_written_only_under_private(tmp_path):
    households = {
        "2026": {
            "household_id": np.arange(5),
            "household_weight": np.ones(5),
            "household_count_people": np.ones(5),
            "decile": np.arange(5),
            "income": np.linspace(1, 2, 5),
        }
    }
    write_result(tmp_path, {"status": "ok", "metrics": []}, households)
    top_level = sorted(p.name for p in tmp_path.iterdir())
    assert top_level == [PRIVATE_DIRECTORY, "result.json"]
    assert (tmp_path / PRIVATE_DIRECTORY / HOUSEHOLDS_FILE).exists()
    result, loaded = read_result(tmp_path)
    assert json.loads((tmp_path / "result.json").read_text()) == result
    assert np.array_equal(loaded["2026"]["income"], households["2026"]["income"])


def test_a_failed_run_always_replaces_an_earlier_comment():
    """Even a run that failed before the comparison posts a failing comment."""
    post = next(s for s in steps() if s.get("name", "").startswith("Post or update"))
    assert post["if"] == "always() && github.event_name == 'pull_request'"
    assert "if [ ! -s report/comment.md ]" in post["run"]
    assert "FAIL" in post["run"]


# The comparison base.

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
SHA = "0123456789abcdef0123456789abcdef01234567"


def step_named(name):
    return next(s for s in steps() if s.get("name") == name)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    ).stdout.strip()


def run_step(name, workspace, **env):
    """Run a step's script in ``workspace`` as Actions runs it.

    Each variable in the step's ``env`` is set, empty unless given, as an
    expression with no value is. Returns the process and the outputs the
    step wrote to ``GITHUB_OUTPUT``.
    """
    step = step_named(name)
    outputs = Path(workspace) / "github_output"
    outputs.write_text("")
    variables = {key: "" for key in step.get("env", {})}
    variables.update(env)
    process = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]],
        cwd=workspace,
        env={**GIT_ENV, **variables, "GITHUB_OUTPUT": str(outputs)},
        capture_output=True,
        text=True,
    )
    written = dict(line.split("=", 1) for line in outputs.read_text().splitlines())
    return process, written


class Origin:
    """A repository on GitHub's side, holding commits made directly."""

    def __init__(self, path):
        path.mkdir(parents=True)
        git(path, "init", "-q")
        # actions/checkout fetches the head by its SHA.
        git(path, "config", "uploadpack.allowAnySHA1InWant", "true")
        self.path = path
        self.tree = git(path, "write-tree")
        self.made = 0

    def commit(self, *parents):
        self.made += 1
        flags = [flag for parent in parents for flag in ("-p", parent)]
        return git(
            self.path, "commit-tree", self.tree, *flags, "-m", f"commit {self.made}"
        )

    def attributed(self, base, head):
        """The commits a comparison of ``base`` with ``head`` counts."""
        return set(git(self.path, "rev-list", f"{base}..{head}").split())


def check_out_the_head(workspace, origin, sha):
    """Fetch ``sha`` into ``workspace/head`` as the workflow's checkout does."""
    depth = step_named("Check out the head")["with"].get("fetch-depth", 1)
    head = Path(workspace) / "head"
    head.mkdir(parents=True)
    git(head, "init", "-q")
    git(head, "fetch", "-q", "--no-tags", f"--depth={depth}", origin.path.as_uri(), sha)
    git(head, "checkout", "-q", "--detach", sha)


def choose_the_base(workspace, origin, merge):
    check_out_the_head(workspace, origin, merge)
    return run_step("Choose the base", workspace, EVENT="pull_request")


def test_a_pull_request_is_compared_with_its_merge_commits_first_parent(tmp_path):
    origin = Origin(tmp_path / "origin")
    # The pull request branches from main at `forked`. The event's
    # pull_request.base.sha can still name it after main has moved on.
    forked = origin.commit(origin.commit())
    change = origin.commit(forked)
    # Main moves on: two later merges.
    tip = origin.commit(origin.commit(forked))
    # GitHub's merge commit for the run: main's tip, then the pull request.
    merge = origin.commit(tip, change)

    process, outputs = choose_the_base(tmp_path / "runner", origin, merge)

    assert process.returncode == 0, process.stdout + process.stderr
    assert outputs == {"sha": tip}
    assert origin.attributed(outputs["sha"], merge) == {merge, change}
    # Against `forked`, main's two later merges counted as the pull request's.
    assert len(origin.attributed(forked, merge) - {merge, change}) == 2


@pytest.mark.parametrize("parents", [0, 1, 3])
def test_a_head_that_does_not_merge_two_commits_has_no_base(tmp_path, parents):
    origin = Origin(tmp_path / "origin")
    head = origin.commit(*[origin.commit() for _ in range(parents)])

    process, outputs = choose_the_base(tmp_path / "runner", origin, head)

    assert process.returncode != 0
    assert f"::error::The head {head} has {parents} parents, not 2" in process.stdout
    assert outputs == {}


def test_the_events_base_sha_is_not_the_comparison_base():
    expressions = re.findall(r"\$\{\{(.*?)\}\}", WORKFLOW.read_text(), re.DOTALL)
    assert expressions
    assert not [e for e in expressions if "pull_request.base.sha" in e]
    names = [s.get("name") for s in steps()]
    order = [
        names.index("Choose the commits"),
        names.index("Check out the head"),
        names.index("Choose the base"),
        names.index("Check out the base"),
    ]
    assert order == sorted(order)
    head = step_named("Check out the head")["with"]
    assert head["ref"] == "${{ steps.commits.outputs.head }}"
    choose = step_named("Choose the base")
    assert choose["id"] == "base"
    assert choose["env"]["BASE"] == "${{ steps.commits.outputs.base }}"
    assert step_named("Check out the base")["with"]["ref"] == (
        "${{ steps.base.outputs.sha }}"
    )


def test_a_pull_request_head_is_its_merge_commit(tmp_path):
    process, outputs = run_step(
        "Choose the commits",
        tmp_path,
        EVENT="pull_request",
        GITHUB_SHA=SHA,
        PR_BASE_REF="main",
        PR_NUMBER="2516",
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert outputs == {
        "base": "",
        "head": SHA,
        "base_name": "main",
        "head_name": "#2516 merged into main",
    }


@pytest.mark.parametrize(
    "inputs, expected",
    [
        (
            {},
            {"base": "main", "head": SHA, "base_name": "main", "head_name": "dev"},
        ),
        (
            {"INPUT_BASE": "2.139.0", "INPUT_HEAD": "fix"},
            {
                "base": "2.139.0",
                "head": "fix",
                "base_name": "2.139.0",
                "head_name": "fix",
            },
        ),
    ],
)
def test_a_dispatch_compares_the_commits_it_names(tmp_path, inputs, expected):
    process, outputs = run_step(
        "Choose the commits",
        tmp_path,
        EVENT="workflow_dispatch",
        GITHUB_SHA=SHA,
        GITHUB_REF_NAME="dev",
        **inputs,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert outputs == expected
    # The base passes through, with no head to read it from.
    process, outputs = run_step(
        "Choose the base", tmp_path, EVENT="workflow_dispatch", BASE=expected["base"]
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert outputs == {"sha": expected["base"]}


@settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    before=st.integers(0, 2),
    events=st.lists(st.sampled_from(["main", "pull request", "update"]), max_size=8),
)
def test_no_commit_of_the_base_branch_counts_as_the_pull_requests(before, events):
    """Invariant 1, for any history: main's commits before and after the
    fork, the pull request's commits, and merges of main into the pull
    request ("Update branch")."""
    with tempfile.TemporaryDirectory() as directory:
        origin = Origin(Path(directory) / "origin")
        main = origin.commit()
        for _ in range(before):
            main = origin.commit(main)
        pull_request = origin.commit(main)
        own = {pull_request}
        merged = main
        for event in events:
            if event == "main":
                main = origin.commit(main)
            elif event == "pull request":
                pull_request = origin.commit(pull_request)
                own.add(pull_request)
            elif main != merged:
                pull_request = origin.commit(pull_request, main)
                own.add(pull_request)
                merged = main
        merge = origin.commit(main, pull_request)

        process, outputs = choose_the_base(Path(directory) / "runner", origin, merge)

        assert process.returncode == 0, process.stdout + process.stderr
        assert outputs == {"sha": main}
        assert origin.attributed(outputs["sha"], merge) == own | {merge}


# Runs with no data access.


def test_a_dependabot_run_is_reported_as_skipped_and_passes(tmp_path):
    """Dependabot gets no secrets, so nothing is measured, and the job passes.

    Runs the measure and compare steps as a Dependabot run does, with the
    head's own tool and a Python that can import its dependencies.
    """
    head = tmp_path / "head"
    shutil.copytree(
        REPO / "policyengine_uk" / "utils" / "aggregate_impact",
        head / "policyengine_uk" / "utils" / "aggregate_impact",
    )
    python = head / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    python.chmod(0o755)
    (tmp_path / "runner_temp").mkdir()
    runner = {
        "RUNNER_TEMP": str(tmp_path / "runner_temp"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "step_summary.md"),
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "PolicyEngine/policyengine-uk",
        "GITHUB_RUN_ID": "1",
    }

    measured, _ = run_step(
        "Measure base, then head", tmp_path, ACTOR="dependabot[bot]", **runner
    )
    assert measured.returncode == 0, measured.stdout + measured.stderr
    assert "Dependabot runs have no data access" in measured.stdout

    compared, outputs = run_step("Compare base with head", tmp_path, **runner)
    assert compared.returncode == 0, compared.stdout + compared.stderr
    assert outputs["status"] == "0", compared.stdout + compared.stderr
    comment = (tmp_path / "report" / "comment.md").read_text()
    assert "## Aggregate impact on certified data: skipped" in comment
    assert step_named("Fail on a structural failure")["if"] == (
        "steps.compare.outputs.status != '0'"
    )


def test_only_dependabot_may_skip_a_run_with_no_data_access(tmp_path):
    """Any other run with no token fails the job instead of skipping."""
    shutil.copytree(
        REPO / "policyengine_uk" / "utils" / "aggregate_impact",
        tmp_path / "head" / "policyengine_uk" / "utils" / "aggregate_impact",
    )
    (tmp_path / "runner_temp").mkdir()
    measured, _ = run_step(
        "Measure base, then head",
        tmp_path,
        ACTOR="a-maintainer",
        RUNNER_TEMP=str(tmp_path / "runner_temp"),
    )
    assert measured.returncode != 0
    assert "::error::HUGGING_FACE_TOKEN is not available" in measured.stdout
    assert not (tmp_path / "measured" / "head" / "result.json").exists()
