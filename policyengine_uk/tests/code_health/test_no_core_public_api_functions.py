"""No code here may use the policyengine-core functions that call the Public API.

``Reform.from_api``, ``Reform.api_id`` and ``policyengine_core.charts.api``
send HTTP requests to api.policyengine.org, and policyengine-core is removing
them. ``policyengine_core.charts`` also re-exports that module's
``decile_chart`` and ``intra_decile_chart``. Code that uses any of them,
including a test that replaces ``requests`` in
``policyengine_core.reforms.reform``, fails once a policyengine-core release
without them is installed. Build reforms with ``Reform.from_dict`` instead.
"""

import re
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
THIS_FILE = Path(__file__).resolve()

REMOVED_CORE_FUNCTION_PATTERN = re.compile(
    r"\.from_api\b"
    r"|\.api_id\b"
    r"|policyengine_core\.charts\.api\b"
    r"|\bget_api_chart_data\b"
    r"|\bdecile_chart\b"
    r"|\bintra_decile_chart\b"
    r"|policyengine_core\.reforms\.reform\.requests\b"
)


def find_removed_core_function_references(source_text: str) -> list[str]:
    return sorted(
        {
            match.group(0)
            for match in REMOVED_CORE_FUNCTION_PATTERN.finditer(source_text)
        }
    )


@pytest.mark.parametrize(
    "source_text, expected_reference",
    [
        pytest.param(
            'Reform.from_api("1", country_id="uk")', ".from_api", id="from_api"
        ),
        pytest.param("policy_id = reform.api_id", ".api_id", id="api_id"),
        pytest.param(
            "from policyengine_core.charts.api import get_api_chart_data",
            "policyengine_core.charts.api",
            id="chart_module",
        ),
        pytest.param(
            "chart_data = get_api_chart_data()",
            "get_api_chart_data",
            id="get_api_chart_data",
        ),
        pytest.param(
            "from policyengine_core.charts import decile_chart",
            "decile_chart",
            id="re_exported_decile_chart",
        ),
        pytest.param(
            "from policyengine_core.charts import intra_decile_chart",
            "intra_decile_chart",
            id="re_exported_intra_decile_chart",
        ),
        pytest.param(
            'monkeypatch.setattr("policyengine_core.reforms.reform.requests.get", '
            "fake_get)",
            "policyengine_core.reforms.reform.requests",
            id="replaced_requests_get",
        ),
    ],
)
def test_pattern_finds_each_removed_function(source_text, expected_reference):
    assert expected_reference in find_removed_core_function_references(source_text)


@pytest.mark.parametrize(
    "source_text",
    [
        pytest.param('Reform.from_dict(changes, country_id="uk")', id="from_dict"),
        pytest.param(
            "from policyengine_core.charts import format_fig, BLUE",
            id="chart_formatting",
        ),
    ],
)
def test_pattern_ignores_core_functions_that_stay(source_text):
    assert find_removed_core_function_references(source_text) == []


def test_package_does_not_use_core_public_api_functions():
    references_by_file = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path.resolve() == THIS_FILE:
            continue
        references = find_removed_core_function_references(path.read_text())
        if references:
            references_by_file[str(path.relative_to(PACKAGE_ROOT))] = references
    assert not references_by_file, (
        "These files use policyengine-core functions that call the Public API "
        f"and are being removed: {references_by_file}. Build reforms with "
        "Reform.from_dict instead."
    )
