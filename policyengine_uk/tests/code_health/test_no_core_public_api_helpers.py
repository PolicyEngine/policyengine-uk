"""No code here may use the policyengine-core helpers that call the Public API.

``Reform.from_api``, ``Reform.api_id`` and ``policyengine_core.charts.api``
send HTTP requests to api.policyengine.org, and policyengine-core is removing
them. Code that still uses them, including a test that replaces
``requests.get`` in ``policyengine_core.reforms.reform``, fails as soon as a
policyengine-core release without them is installed.
"""

import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
THIS_FILE = Path(__file__).resolve()

REMOVED_HELPER_REFERENCE = re.compile(
    r"\.from_api\b"
    r"|\.api_id\b"
    r"|policyengine_core\.charts\.api\b"
    r"|\bget_api_chart_data\b"
    r"|policyengine_core\.reforms\.reform\.requests\b"
)


def test_code_does_not_use_core_public_api_helpers():
    references_by_file = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path.resolve() == THIS_FILE:
            continue
        references = sorted(
            {
                match.group(0)
                for match in REMOVED_HELPER_REFERENCE.finditer(path.read_text())
            }
        )
        if references:
            references_by_file[str(path.relative_to(PACKAGE_ROOT))] = references
    assert not references_by_file, (
        f"These files use policyengine-core helpers that call the Public API "
        f"over HTTP and are being removed: {references_by_file}. Build reforms "
        "with Reform.from_dict instead."
    )
