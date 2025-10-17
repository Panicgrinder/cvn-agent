from __future__ import annotations
from typing import Any

from utils.eval_cache import EvalCache, make_key


def test_make_key_stable_for_equivalent_dicts() -> None:
    a: dict[str, Any] = {"x": 1, "y": [3, 2, 1], "z": {"a": 1, "b": 2}}
    b: dict[str, Any] = {"z": {"b": 2, "a": 1}, "y": [3, 2, 1], "x": 1}
    # Reihenfolge der Keys darf den Hash nicht verändern
    assert make_key(a) == make_key(b)


def test_eval_cache_put_get_persist(tmp_path: "Any") -> None:
    p = tmp_path / "cache.jsonl"
    cache = EvalCache(str(p))
    key = make_key({"a": 1, "b": 2})
    assert cache.get(key) is None
    value = {"content": "answer", "finish_reason": "stop"}
    cache.put(key, value)
    # gleicher Prozess
    assert cache.get(key) == value
    # neue Instanz liest aus Datei
    cache2 = EvalCache(str(p))
    assert cache2.get(key) == value
