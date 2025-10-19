from __future__ import annotations

import importlib
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_to_module_name_cross_drive_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.audit_workspace")
    # Simuliere Pfad auf anderem Laufwerk durch künstliche PROJECT_ROOT
    fake_root = str(tmp_path / "Xroot")
    monkeypatch.setattr(mod, "PROJECT_ROOT", fake_root)
    # Datei liegt unter einem anderen Prefix → Fallback sollte basename nehmen
    other = str(tmp_path / "Ydrive" / "pkg" / "mod.py")
    (tmp_path / "Ydrive" / "pkg").mkdir(parents=True)
    (tmp_path / "Ydrive" / "pkg" / "mod.py").write_text("print(1)\n", encoding="utf-8")

    m = mod.to_module_name(other)
    assert m.endswith("pkg.mod") or m == "mod"
