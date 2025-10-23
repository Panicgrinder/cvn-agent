from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, Any, List, Mapping, Iterator, cast

import pytest

from app.core import content_management as cm


@pytest.fixture()
def policy_file_profiles() -> Iterator[str]:
    # default forbids 'bad', rewrites 'tea'->'coffee'
    # profile 'eval' forbids 'evalban', rewrites 'foo'->'bar'
    data: Dict[str, Any] = {
        "default": {
            "forbidden_terms": ["bad"],
            "rewrite_map": {"tea": "coffee"},
        },
        "profiles": {
            "eval": {
                "forbidden_terms": ["evalban"],
                "rewrite_map": {"foo": "bar"},
            },
            "alt": {
                "rewrite_map": {"color": "colour"}
            },
        },
    }
    fd, path = tempfile.mkstemp(prefix="policy_profiles_", suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def _msgs(txt: str) -> List[Dict[str, str]]:
    return [{"role": "user", "content": txt}]


def test_allow_path(monkeypatch: pytest.MonkeyPatch, policy_file_profiles: str) -> None:
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", policy_file_profiles, raising=False)

    # Contains no forbidden or rewrite terms
    pre = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("hello world")), mode="default")
    assert pre.action == "allow"
    post = cm.apply_post("ok then", mode="default")
    assert post.action == "allow"


def test_rewrite_and_block_default(monkeypatch: pytest.MonkeyPatch, policy_file_profiles: str) -> None:
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", policy_file_profiles, raising=False)

    # Rewrite via default map
    pre = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("tea time")), mode="default")
    assert pre.action in {"allow", "rewrite"}
    if pre.action == "rewrite":
        joined = "\n".join(m.get("content", "") for m in cast(List[Dict[str, str]], pre.messages or []))
        assert "coffee" in joined and "tea" not in joined

    # Block via default forbidden term
    pre2 = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("very bad idea")), mode="default")
    assert pre2.action == "block"


def test_profile_merge_eval(monkeypatch: pytest.MonkeyPatch, policy_file_profiles: str) -> None:
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", policy_file_profiles, raising=False)

    # mode=eval should map to profile 'eval' overlay
    pre = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("foo and tea")), mode="eval")
    # Expect both rewrites available (default tea->coffee and eval foo->bar)
    if pre.action == "rewrite" and pre.messages:
        text = "\n".join(m.get("content", "") for m in cast(List[Dict[str, str]], pre.messages))
        assert "bar" in text and "coffee" in text and "foo" not in text and "tea" not in text

    # Forbidden in eval profile
    pre2 = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("evalban is here")), mode="eval")
    assert pre2.action == "block"


def test_unrestricted_bypass(monkeypatch: pytest.MonkeyPatch, policy_file_profiles: str) -> None:
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", policy_file_profiles, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_STRICT_UNRESTRICTED_BYPASS", True, raising=False)

    # Even with forbidden term, unrestricted mode should bypass and allow
    pre = cm.apply_pre(cast(List[Mapping[str, Any]], _msgs("this is bad")), mode="unrestricted")
    assert pre.action == "allow"
    post = cm.apply_post("answer with evalban", mode="unrestricted")
    assert post.action == "allow"
