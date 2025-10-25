import importlib
import pytest
from _pytest.monkeypatch import MonkeyPatch

@pytest.mark.unit
def test_tools_whitelist_denies_by_default(monkeypatch: MonkeyPatch):
    # Ensure tools disabled
    monkeypatch.setenv("TOOLS_ENABLED", "false")
    # reload settings and registry to pick up env
    import app.core.settings as settings_mod
    importlib.reload(settings_mod)
    from app.tools import registry as reg
    importlib.reload(reg)

    # calc_add is registered by default but should not be allowed
    assert "calc_add" in reg.list_tools()
    out = reg.call_tool("calc_add", {"a": 1, "b": 2})
    assert out.get("ok") is False
    assert "not allowed" in out.get("error", "")


@pytest.mark.unit
def test_tools_whitelist_allows_listed(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("TOOLS_ENABLED", "true")
    monkeypatch.setenv("TOOLS_WHITELIST", "[\"calc_add\"]")
    # reload settings and registry
    import app.core.settings as settings_mod
    importlib.reload(settings_mod)
    from app.tools import registry as reg
    importlib.reload(reg)

    assert "calc_add" in reg.list_tools()
    out = reg.call_tool("calc_add", {"a": 1, "b": 2})
    assert out == {"ok": True, "data": {"result": 3.0}}


@pytest.mark.unit
def test_tools_unknown_tool(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("TOOLS_ENABLED", "true")
    monkeypatch.setenv("TOOLS_WHITELIST", "[\"calc_add\"]")
    import app.core.settings as settings_mod
    importlib.reload(settings_mod)
    from app.tools import registry as reg
    importlib.reload(reg)

    out = reg.call_tool("does_not_exist", {})
    assert out.get("ok") is False
    assert "unknown tool" in out.get("error", "")
