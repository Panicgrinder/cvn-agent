import os
import sys
import json
import tempfile
import importlib
from typing import Any, cast


def _reload_run_eval() -> Any:
    # Sorgt dafür, dass Änderungen an Modul-Globals greifen
    name = "scripts.run_eval"
    importlib.invalidate_caches()
    if name in sys.modules:
        importlib.reload(sys.modules[name])
    else:
        importlib.import_module(name)
    return cast(Any, sys.modules[name])


def test_synonyms_overlay_merged_and_deduped():
    run_eval = _reload_run_eval()
    old_cfg = getattr(run_eval, "DEFAULT_CONFIG_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "config")
            os.makedirs(cfg, exist_ok=True)
            base_path = os.path.join(cfg, "synonyms.json")
            overlay_path = os.path.join(cfg, "synonyms.local.json")
            with open(base_path, "w", encoding="utf-8") as f:
                json.dump({
                    "arzt": ["doktor", "mediziner"],
                    "unternehmen": ["firma"]
                }, f, ensure_ascii=False)
            with open(overlay_path, "w", encoding="utf-8") as f:
                json.dump({
                    "arzt": ["arzt", "ärztin", "mediziner"],
                    "unternehmen": ["betrieb"]
                }, f, ensure_ascii=False)

            # Patch Config-Dir und Cache leeren
            mod = cast(Any, run_eval)
            mod.DEFAULT_CONFIG_DIR = cfg
            mod._synonyms_cache = None

            syns_arzt = mod.get_synonyms("arzt")
            # Erwartet: Merge + Dedupe (doktor, mediziner, ärztin mindestens)
            for w in ("doktor", "mediziner", "ärztin"):
                assert w in syns_arzt, f"'{w}' fehlt in gemergten Synonymen: {syns_arzt}"

            syns_unternehmen = mod.get_synonyms("unternehmen")
            for w in ("firma", "betrieb"):
                assert w in syns_unternehmen, f"'{w}' fehlt in gemergten Synonymen: {syns_unternehmen}"
    finally:
        # Restore
        mod2 = cast(Any, run_eval)
        mod2.DEFAULT_CONFIG_DIR = old_cfg
        mod2._synonyms_cache = None


def test_synonyms_overlay_missing_is_silent():
    run_eval = _reload_run_eval()
    old_cfg = getattr(run_eval, "DEFAULT_CONFIG_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "config")
            os.makedirs(cfg, exist_ok=True)
            base_path = os.path.join(cfg, "synonyms.json")
            with open(base_path, "w", encoding="utf-8") as f:
                json.dump({
                    "sicherheit": ["schutz", "sicher"]
                }, f, ensure_ascii=False)

            # Kein overlay schreiben
            mod = cast(Any, run_eval)
            mod.DEFAULT_CONFIG_DIR = cfg
            mod._synonyms_cache = None

            syns = mod.get_synonyms("sicherheit")
            assert "schutz" in syns and "sicher" in syns
    finally:
        mod2 = cast(Any, run_eval)
        mod2.DEFAULT_CONFIG_DIR = old_cfg
        mod2._synonyms_cache = None
