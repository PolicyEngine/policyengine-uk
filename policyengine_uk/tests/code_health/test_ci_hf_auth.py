"""CI reads the gated dataset with short-lived tokens, never a stored secret.

The microsimulation tests read policyengine-uk-data-private on Hugging Face.
``.github/workflows/test-suite.yaml`` runs each step that needs it under
``.github/with-hf-token.sh``, which exchanges the job's GitHub OIDC token for a
one-hour, read-only token from the policyengine-auto account's CI/CD identity
(Hugging Face Trusted Publishers). These tests hold the workflows and the
helper to the invariants that keep it that way:

1. No workflow reads a Hugging Face secret (dotted or bracket form, any case),
   passes every secret on, or sets a token variable itself.
2. The two pytest steps are the only ones that exchange, each for the
   read-only identity (a repo resource would be a write token), optionally (a
   run without OIDC goes on without credentials), and each runs exactly one
   pinned command, its one pytest through the helper. No other pytest runs in
   the suite.
3. The helper comes from a separate, unconditional checkout of this
   workflow's commit, right after the main one, so a release test of an older
   version commit still has it.
4. No exchange's output is redirected: the line that masks the token must
   reach the runner, not a file such as the uploaded test list.
5. Every job in the suite can request an OIDC token; every caller grants it
   and passes no secrets.
6. Every caller of the suite has a CI/CD identity in ``IDENTITIES``, and a
   caller that runs on a pull request, merge group or manual dispatch has one
   that matches any branch.
7. Result's own shell, run with and without OIDC and with and without
   ``require-data``, reports the dataset present exactly when the run has
   OIDC, and fails a run that requires the data and has none.
8. The helper runs the command with the token, its arguments and exit
   status, masks the token first, and never runs it without one unless the
   run has no OIDC and the token is optional.
"""

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_DIR = REPO_ROOT / ".github"
HELPER = GITHUB_DIR / "with-hf-token.sh"
WORKFLOWS = GITHUB_DIR / "workflows"
TEST_SUITE = WORKFLOWS / "test-suite.yaml"
SUITE_USES = "./.github/workflows/test-suite.yaml"
CI_IDENTITY = "policyengine-auto"
# Where the suite's jobs check out the helper from this workflow's commit.
HELPER_IN_CI = ".ci-tools/.github/with-hf-token.sh"
# The policyengine-auto CI/CD identities this repository needs on Hugging
# Face: calling workflow -> the branch it is pinned to (None: any ref). An
# identity matches the workflow that starts the run, not test-suite.yaml.
IDENTITIES = {
    "code_changes.yaml": None,
    "pr_code_changes.yaml": None,
    "versioning.yaml": None,
}
# The exact command each exchanging step runs, whitespace collapsed.
COLLECT = (
    f'{HELPER_IN_CI} bash -c \'pytest "$TESTS" --rootdir "$ROOTDIR" '
    "-c pyproject.toml --collect-only -q -p no:cacheprovider > collected.txt'"
)
SHARD = (
    f'PYTHONPATH="$GITHUB_WORKSPACE/.github" {HELPER_IN_CI} pytest "$TESTS" '
    '--rootdir "$ROOTDIR" -c pyproject.toml -p no:cacheprovider '
    '-p pytest_outcome_log --outcome-log="$OUTCOMES" -o xfail_strict=true '
    '--maxfail=0 -v -n 4 --dist worksteal --shard "$SHARD" "${coverage[@]}"'
)

if not HELPER.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )


def _workflows():
    for path in sorted([*WORKFLOWS.glob("*.yaml"), *WORKFLOWS.glob("*.yml")]):
        yield path.name, yaml.safe_load(path.read_text())


def _suite() -> dict:
    return yaml.safe_load(TEST_SUITE.read_text())


def _env_scopes():
    for name, workflow in _workflows():
        yield name, "workflow", workflow.get("env") or {}
        for job_name, job in (workflow.get("jobs") or {}).items():
            yield name, job_name, job.get("env") or {}
            for step in job.get("steps") or []:
                yield name, f"{job_name}/{step.get('name')}", step.get("env") or {}


def _commands(run: str) -> list[str]:
    """The shell lines a run script executes, continuations joined."""
    lines = run.replace("\\\n", " ").splitlines()
    return [
        " ".join(l.split())
        for l in lines
        if l.strip() and not l.lstrip().startswith("#")
    ]


def _helper_steps():
    for name, workflow in _workflows():
        for job_name, job in (workflow.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if any("with-hf-token.sh" in c for c in _commands(step.get("run", ""))):
                    yield name, job_name, step


def _step(job: str, name: str) -> dict:
    (step,) = [s for s in _suite()["jobs"][job]["steps"] if s.get("name") == name]
    return step


def test_no_workflow_reads_a_hugging_face_secret():
    pattern = re.compile(
        r"secrets\s*(\.\s*\w*(HF|HUGGING)\w*|\[\s*['\"][^'\"]*(HF|HUGGING)[^'\"]*['\"]\s*\])",
        re.IGNORECASE,
    )
    # Passing every secret on also reaches the org-wide token.
    passes_all = re.compile(
        r"secrets:\s*inherit|toJSON\(\s*secrets\s*\)", re.IGNORECASE
    )
    for path in sorted([*WORKFLOWS.glob("*.yaml"), *WORKFLOWS.glob("*.yml")]):
        text = path.read_text()
        assert not pattern.search(text), path.name
        assert not passes_all.search(text), path.name


def test_no_workflow_sets_a_token_variable_itself():
    for name, scope, env in _env_scopes():
        for variable in ("HUGGING_FACE_TOKEN", "HF_TOKEN"):
            assert variable not in env, f"{name} {scope} sets {variable}"


def test_only_the_two_pytest_steps_exchange_and_only_for_the_identity():
    found = {(name, job, step["name"]) for name, job, step in _helper_steps()}
    assert found == {
        ("test-suite.yaml", "YAML", "List the Python tests"),
        ("test-suite.yaml", "Python", "Run the tests"),
    }
    for _, _, step in _helper_steps():
        assert step["env"]["HF_OIDC_RESOURCE"] == CI_IDENTITY
        assert step["env"]["HF_OIDC_OPTIONAL"] == "1"
    for name, scope, env in _env_scopes():
        if "HF_OIDC_RESOURCE" in env:
            assert env["HF_OIDC_RESOURCE"] == CI_IDENTITY, f"{name} {scope}"


def test_each_pytest_step_runs_exactly_its_wrapped_command():
    assert _commands(_step("YAML", "List the Python tests")["run"]) == [
        COLLECT,
        "tail -n 1 collected.txt",
    ]
    shard = [
        c for c in _commands(_step("Python", "Run the tests")["run"]) if "pytest" in c
    ]
    # The whole command, so nothing can be chained onto it with && or ;.
    assert shard == [SHARD]


def test_no_other_step_in_the_suite_runs_pytest():
    exchanging = {"List the Python tests", "Run the tests"}
    for job_name, job in _suite()["jobs"].items():
        for step in job.get("steps") or []:
            if step.get("name") in exchanging:
                continue
            for command in _commands(step.get("run", "")):
                assert not re.search(r"\bpytest\b", command), (job_name, command)


def test_the_helper_comes_from_this_workflows_commit():
    for job_name in ("YAML", "Python"):
        steps = _suite()["jobs"][job_name]["steps"]
        names = [s.get("name") for s in steps]
        (checkout,) = [
            s for s in steps if s.get("name") == "Check out the token helper"
        ]
        assert checkout["uses"].startswith("actions/checkout@")
        assert checkout["with"]["ref"] == "${{ github.sha }}"
        assert checkout["with"]["path"] == ".ci-tools"
        assert checkout["with"]["sparse-checkout"] == ".github/with-hf-token.sh"
        # Right after the main checkout, which would delete .ci-tools if it
        # ran later, and unconditional, so every exchanging step has it.
        assert (
            names.index("Check out the token helper")
            == names.index("Checkout repo") + 1
        )
        assert "if" not in checkout


def test_no_exchange_output_is_redirected():
    for name, job, step in _helper_steps():
        for command in _commands(step["run"]):
            if "with-hf-token.sh" in command:
                outside_quotes = re.sub(r"'[^']*'", "''", command)
                assert not re.search(r"[>|]", outside_quotes), (
                    f"{name} {job}: {command}"
                )


def test_every_job_can_request_an_oidc_token():
    suite = _suite()
    assert suite["permissions"]["id-token"] == "write"
    for job_name, job in suite["jobs"].items():
        if "permissions" in job:
            assert job["permissions"].get("id-token") == "write", job_name
    for name, workflow in _workflows():
        for job_name, job in (workflow.get("jobs") or {}).items():
            if job.get("uses") == SUITE_USES:
                assert job["permissions"]["id-token"] == "write", (name, job_name)
                assert "secrets" not in job, (name, job_name)


def test_every_caller_has_an_identity_that_matches_its_refs():
    callers = {}
    for name, workflow in _workflows():
        if any(
            j.get("uses") == SUITE_USES for j in (workflow.get("jobs") or {}).values()
        ):
            on = workflow.get(True, workflow.get("on"))  # PyYAML reads `on` as True
            callers[name] = set(on) if isinstance(on, (dict, list)) else {on}
    assert set(callers) == set(IDENTITIES)
    for name, events in callers.items():
        if events & {
            "pull_request",
            "pull_request_target",
            "merge_group",
            "workflow_dispatch",
        }:
            assert IDENTITIES[name] is None, (
                f"{name} runs off main, so its identity needs any branch"
            )


RESULT_CASES = [
    # OIDC, require-data -> exit status, --data passed to the checker
    (True, "true", 0, "present"),
    (True, "false", 0, "present"),
    (False, "false", 0, "absent"),
    (False, "true", 1, None),
]


@pytest.mark.parametrize("oidc,require,status,data", RESULT_CASES)
def test_result_reports_the_dataset_exactly_when_the_run_has_oidc(
    tmp_path, oidc, require, status, data
):
    """Run Result's own shell against a stub checker that records its arguments."""
    (check,) = [
        s
        for s in _suite()["jobs"]["Result"]["steps"]
        if "check_test_shards.py" in s.get("run", "")
    ]
    assert "${{" not in check["run"]
    assert check["env"]["REQUIRE_DATA"] == "${{ inputs.require-data }}"
    assert (
        check["env"]["MODE"]
        == "${{ inputs.dist-artifact == '' && 'source' || 'wheel' }}"
    )
    stub = tmp_path / ".github" / "check_test_shards.py"
    stub.parent.mkdir()
    stub.write_text(
        "import json, sys; open('argv.json', 'w').write(json.dumps(sys.argv[1:]))"
    )
    env = {"PATH": os.environ["PATH"], "MODE": "source", "REQUIRE_DATA": require}
    if oidc:
        env["ACTIONS_ID_TOKEN_REQUEST_URL"] = "https://example.invalid/oidc"
    result = subprocess.run(
        ["bash", "-e", "-c", check["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == status, result.stdout + result.stderr
    argv_file = tmp_path / "argv.json"
    if data is None:
        assert not argv_file.exists()
        assert "::error::" in result.stdout
    else:
        argv = json.loads(argv_file.read_text())
        assert argv[argv.index("--data") + 1] == data


# The helper, run against a fake exchange: a `uvx` that records its arguments
# and the resource it saw, prints $FAKE_TOKEN and exits with $FAKE_EXIT.

FAKE_UVX = """#!/bin/sh
printf '%s\\n' "$*" > "$CALLS/uvx"
printf '%s' "${HF_OIDC_RESOURCE:-}" > "$CALLS/resource"
printf '%s' "$FAKE_TOKEN"
exit "${FAKE_EXIT:-0}"
"""

CHILD = (
    "import json, os, sys;"
    "print(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read(),"
    " 'env': {k: os.environ.get(k) for k in ("
    "'HUGGING_FACE_TOKEN', 'HF_TOKEN', 'HF_OIDC_RESOURCE', 'HF_OIDC_OPTIONAL')}}));"
    "open(os.environ['CALLS'] + '/child', 'w').close();"
    "sys.exit(int(os.environ.get('CHILD_EXIT', '0')))"
)


@pytest.fixture
def helper(tmp_path):
    calls = tmp_path / "calls"
    calls.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uvx = bin_dir / "uvx"
    uvx.write_text(FAKE_UVX)
    uvx.chmod(uvx.stat().st_mode | stat.S_IEXEC)

    def run(*args, stdin="", **env):
        base = {
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "CALLS": str(calls),
            "FAKE_TOKEN": "hf_jwt_fake",
            "HF_OIDC_RESOURCE": CI_IDENTITY,
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.invalid/oidc",
        }
        for key, value in env.items():
            if value is None:
                base.pop(key, None)
            else:
                base[key] = value
        return subprocess.run(
            ["bash", str(HELPER), *(args or (sys.executable, "-c", CHILD))],
            input=stdin,
            capture_output=True,
            text=True,
            env=base,
        )

    run.calls = calls
    return run


def _child(result):
    (line,) = [l for l in result.stdout.splitlines() if l.startswith("{")]
    return json.loads(line)


def test_helper_runs_the_command_with_a_masked_token(helper):
    result = helper(
        sys.executable,
        "-c",
        CHILD,
        "two words",
        "$HOME",
        stdin="in\n",
        CHILD_EXIT="3",
    )
    assert result.returncode == 3
    assert result.stdout.splitlines()[0] == "::add-mask::hf_jwt_fake"
    out = _child(result)
    assert out["argv"] == ["two words", "$HOME"]
    assert out["stdin"] == "in\n"
    assert out["env"] == {
        "HUGGING_FACE_TOKEN": "hf_jwt_fake",
        "HF_TOKEN": "hf_jwt_fake",
        # huggingface_hub >= 1.19 would run its own exchange if this were set.
        "HF_OIDC_RESOURCE": None,
        "HF_OIDC_OPTIONAL": None,
    }
    assert (helper.calls / "uvx").read_text().split() == [
        "--from",
        "huggingface_hub==2.2.0",
        "hf",
        "auth",
        "token",
    ]
    assert (helper.calls / "resource").read_text() == CI_IDENTITY


@pytest.mark.parametrize(
    "env",
    [
        {"FAKE_EXIT": "1"},
        {"FAKE_TOKEN": ""},
        {"HF_OIDC_RESOURCE": None},
        # Optional only means "no OIDC in this run"; with OIDC, a failed
        # exchange still fails the step.
        {"FAKE_EXIT": "1", "HF_OIDC_OPTIONAL": "1"},
        # Without OIDC and without the optional flag, it still tries.
        {"FAKE_EXIT": "1", "ACTIONS_ID_TOKEN_REQUEST_URL": None},
    ],
    ids=[
        "exchange-fails",
        "empty-token",
        "no-resource",
        "optional-with-oidc",
        "strict-without-oidc",
    ],
)
def test_helper_never_runs_the_command_without_a_token(helper, env):
    result = helper(**env)
    assert result.returncode != 0
    assert not (helper.calls / "child").exists()
    assert "::add-mask::" not in result.stdout


def test_helper_runs_without_a_token_only_when_optional_and_no_oidc(helper):
    result = helper(ACTIONS_ID_TOKEN_REQUEST_URL=None, HF_OIDC_OPTIONAL="1")
    assert result.returncode == 0, result.stderr
    assert not (helper.calls / "uvx").exists()
    assert all(value is None for value in _child(result)["env"].values())
