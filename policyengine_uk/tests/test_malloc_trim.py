"""The conftest hands freed memory back to the system after each test file.

It calls glibc's malloc_trim(0) once a file's last test has been torn down,
and only then. With glibc it must find the function, or the release would
silently do nothing.
"""

import platform
from pathlib import Path
from types import SimpleNamespace

import pytest


def _conftest(request):
    path = Path(__file__).with_name("conftest.py")
    for plugin in request.config.pluginmanager.get_plugins():
        if getattr(plugin, "__file__", None) and Path(plugin.__file__) == path:
            return plugin
    raise AssertionError(f"{path} is not loaded as a plugin")


def test_malloc_trim_is_found_with_glibc(request):
    if platform.libc_ver()[0] != "glibc":
        pytest.skip("malloc_trim is part of glibc")
    assert _conftest(request)._malloc_trim is not None


@pytest.mark.parametrize(
    "next_file, trims",
    [("test_a.py", False), ("test_b.py", True), (None, True)],
    ids=["same file", "another file", "last test"],
)
def test_trims_only_after_a_files_last_test(request, monkeypatch, next_file, trims):
    conftest = _conftest(request)
    calls = []
    monkeypatch.setattr(conftest, "_malloc_trim", calls.append)
    item = SimpleNamespace(path=Path("test_a.py"))
    nextitem = None if next_file is None else SimpleNamespace(path=Path(next_file))

    conftest.pytest_runtest_teardown(item, nextitem)

    assert calls == ([0] if trims else [])
