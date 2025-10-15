import unittest
import pytest
from unittest.mock import patch
from typing import Any, Dict, List, Optional
import sys
import os

# Cache für importierte Module
_run_eval_module = None

def _get_run_eval():
    """Cached import of run_eval module for better performance."""
    global _run_eval_module
    if _run_eval_module is None:
        # Add project root to path if needed
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from scripts import run_eval as _run_eval
        _run_eval_module = _run_eval
    return _run_eval_module


class ResponseStub:
    status_code = 200

    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self):
        return None

    def json(self) -> Dict[str, Any]:
        # scripts.run_eval.evaluate_item erwartet ein Top-Level "content"
        return {"content": self._content}


class FakeClient:
    def __init__(self, content: str):
        self._content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, json, headers=None):
        return ResponseStub(self._content)


@pytest.mark.unit
@pytest.mark.eval
class TestRPGHeuristics(unittest.IsolatedAsyncioTestCase):
    async def test_rpg_style_score_basic(self):
        run_eval = _get_run_eval()

        rpg_text = (
            "Chronistin von Novapolis\n"
            "Szene: In der alten U-Bahn\n"
            "Konsequenz: Der Lärm lockt Plünderer an\n"
            "Optionen: Verstecken, Fliehen\n"
            "world_state: {...}\n"
            "state_patches: []\n"
        )
        general_text = "Erkläre die Unterschiede zwischen Array und Liste in Python."

        high = run_eval.rpg_style_score(rpg_text)
        low = run_eval.rpg_style_score(general_text)
        assert high >= 0.4
        assert low <= 0.2

    async def _eval_with_content(self, pkg: str, content: str, checks: Optional[List[str]] = None) -> Any:
        run_eval = _get_run_eval()

        # Item aufbauen
        item = run_eval.EvaluationItem(
            id="eval-xyz",
            messages=[{"role": "user", "content": "Test"}],
            checks={"must_include": [], "keywords_any": [], "keywords_at_least": {"count": 0, "items": []}, "not_include": [], "regex": []},
            source_file="demo.jsonl",
            source_package=pkg,
        )

        # httpx.AsyncClient innerhalb des geladenen Moduls patchen
        async def _run():
            def _mk_client(*args, **kwargs):
                return FakeClient(content)

            with patch.object(run_eval, "httpx") as httpx_mod:
                httpx_mod.AsyncClient = _mk_client
                res = await run_eval.evaluate_item(
                    item,
                    api_url="http://dummy/chat",
                    eval_mode=True,
                    client=None,
                    enabled_checks=(checks or ["rpg_style"]),
                    model_override=None,
                    temperature_override=None,
                    host_override=None,
                    top_p_override=None,
                )
                return res

        return await _run()

    async def test_rpg_style_check_behaves_by_package(self):
        rpg_like = (
            "Chronistin von Novapolis\nSzene: Marktplatz\nKonsequenz: ...\nOptionen: ...\nworld_state: {}\n"
        )
        general_text = "Dies ist eine sachliche, technische Erklärung ohne RPG-Elemente."

        # In RPG-Paket sollte rpg_style bestehen
        res1 = await self._eval_with_content("novapolis_rpg", rpg_like)
        assert res1.checks_passed.get("rpg_style") is True
        assert res1.success is True

        # In General-Paket sollte rpg_style bei RPG-Text fehlschlagen
        res2 = await self._eval_with_content("general", rpg_like)
        assert res2.checks_passed.get("rpg_style") is False
        assert res2.success is False

        # In General-Paket sollte rpg_style bei neutralem Text bestehen
        res3 = await self._eval_with_content("general", general_text)
        assert res3.checks_passed.get("rpg_style") is True
        assert res3.success is True
