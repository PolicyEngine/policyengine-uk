"""CI reads the gated dataset with short-lived tokens, never a stored secret.

The microsimulation tests read policyengine-uk-data-private on Hugging Face.
``.github/workflows/test-suite.yaml`` runs each step that needs it under
``.github/with-hf-token.sh``, which exchanges the job's GitHub OIDC token for a
one-hour, read-only token from the policyengine-auto account's CI/CD identity
(Hugging Face Trusted Publishers). These tests hold the workflows and the
helper to the invariants that keep it that way:

1. No workflow reads a Hugging Face secret or sets a token variable itself.
2. Exactly the two pytest steps exchange, both for the read-only identity
   (a repo resource would be a write token) and both optional, so a fork pull
   request, which has no OIDC, runs without credentials as before.
3. No exchange's output is redirected: the line that masks the token must
   reach the runner, not a file such as the uploaded test list.
4. Result decides whether the run had the dataset from OIDC, not a secret.
5. The helper runs the command with the token, its arguments and exit
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
CI_IDENTITY = "policyengine-auto"

if not HELPER.exists():
    pytest.skip(
        "the .github folder is not part of an installed package",
        allow_module_level=True,
    )


def _workflows():
    for path in sorted([*WORKFLOWS.glob("*.yaml"), *WORKFLOWS.glob("*.yml")]):
        yield path.name, yaml.safe_load(path.read_text())


def _env_scopes():
    for name, workflow in _workflows():
        yield name, "workflow", workflow.get("env") or {}
        for job_name, job in (workflow.get("jobs") or {}).items():
            yield name, job_name, job.get("env") or {}
            for step in job.get("steps") or []:
                yield name, f"{job_name}/{step.get('name')}", step.get("env") or {}


def _invokes_helper(run: str) -> bool:
    return any(
        "with-hf-token.sh" in line and not line.lstrip().startswith("#")
        for line in run.splitlines()
    )


def _helper_steps():
    for name, workflow in _workflows():
        for job_name, job in (workflow.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if _invokes_helper(step.get("run", "")):
                    yield name, job_name, step


def test_no_workflow_reads_a_hugging_face_secret():
    pattern = re.compile(r"secrets\.\w*(HF|HUGGING)\w*", re.IGNORECASE)
    for path in sorted([*WORKFLOWS.glob("*.yaml"), *WORKFLOWS.glob("*.yml")]):
        assert not pattern.search(path.read_text()), path.name


def test_no_workflow_sets_a_token_variable_itself():
    for name, scope, env in _env_scopes():
        for variable in ("HUGGING_FACE_TOKEN", "HF_TOKEN"):
            assert variable not in env, f"{name} {scope} sets {variable}"


def test_exactly_the_pytest_steps_exchange_for_the_read_only_identity():
    found = {(name, job, step["name"]) for name, job, step in _helper_steps()}
    assert found == {
        ("test-suite.yaml", "YAML", "List the Python tests"),
        ("test-suite.yaml", "Python", "Run the tests"),
    }
    for _, _, step in _helper_steps():
        assert step["env"]["HF_OIDC_RESOURCE"] == CI_IDENTITY
        assert step["env"]["HF_OIDC_OPTIONAL"] == "1"
        assert re.search(r"with-hf-token\.sh (bash -c ')?pytest ", step["run"])
    for name, scope, env in _env_scopes():
        if "HF_OIDC_RESOURCE" in env:
            assert env["HF_OIDC_RESOURCE"] == CI_IDENTITY, f"{name} {scope}"


def test_no_exchange_output_is_redirected():
    for name, job, step in _helper_steps():
        script = step["run"].replace("\\\n", " ")
        for line in script.splitlines():
            if "with-hf-token.sh" in line and not line.lstrip().startswith("#"):
                outside_quotes = re.sub(r"'[^']*'", "''", line)
                assert not re.search(r"[>|]", outside_quotes), f"{name} {job}: {line}"


def test_jobs_that_exchange_can_request_an_oidc_token():
    suite = yaml.safe_load(TEST_SUITE.read_text())
    assert suite["permissions"]["id-token"] == "write"
    for name, workflow in _workflows():
        for job_name, job in (workflow.get("jobs") or {}).items():
            if job.get("uses") == "./.github/workflows/test-suite.yaml":
                assert job["permissions"]["id-token"] == "write", (name, job_name)
                assert "secrets" not in job, (name, job_name)


def test_result_reads_dataset_access_from_oidc():
    suite = yaml.safe_load(TEST_SUITE.read_text())
    (check,) = [
        step
        for step in suite["jobs"]["Result"]["steps"]
        if "check_test_shards.py" in step.get("run", "")
    ]
    assert "DATA" not in check.get("env", {})
    assert 'if [ -n "${ACTIONS_ID_TOKEN_REQUEST_URL:-}" ]; then' in check["run"]


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
