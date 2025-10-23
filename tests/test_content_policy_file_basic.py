from __future__ import annotations

import json
import os
import tempfile
from typing import List, Dict, Any, Mapping, Iterator, cast

import pytest

from app.core import content_management as cm


@pytest.fixture()
def temp_policy_file() -> Iterator[str]:
    data: Dict[str, Any] = {
        "forbidden_terms": ["badword", "block_me"],
        "rewrite_map": {"foo": "bar", "colour": "color"},
    }
    fd, path = tempfile.mkstemp(prefix="policy_", suffix=".json")
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


def _mk_user_msgs(texts: List[str]) -> List[Dict[str, str]]:
    return [{"role": "user", "content": t} for t in texts]


def test_apply_pre_rewrite_and_block_from_file(monkeypatch: pytest.MonkeyPatch, temp_policy_file: str) -> None:
    # Enable policies and point to temp file
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", temp_policy_file, raising=False)

    # Rewrite case: contains a term from rewrite_map
    msgs = _mk_user_msgs(["hello foo world"])  # foo -> bar
    typed_msgs: List[Mapping[str, Any]] = cast(List[Mapping[str, Any]], msgs)
    pre = cm.apply_pre(typed_msgs, mode="default")
    assert pre.action in {"allow", "rewrite"}
    if pre.action == "rewrite":
        assert pre.messages is not None
        joined = "\n".join(m.get("content", "") for m in pre.messages or [])
        assert "bar" in joined and "foo" not in joined

    # Block case: contains forbidden term
    msgs2 = _mk_user_msgs(["please say badword"])
    typed_msgs2: List[Mapping[str, Any]] = cast(List[Mapping[str, Any]], msgs2)
    pre2 = cm.apply_pre(typed_msgs2, mode="default")
    assert pre2.action == "block"


def test_apply_post_rewrite_and_block_from_file(monkeypatch: pytest.MonkeyPatch, temp_policy_file: str) -> None:
    # Enable policies and point to temp file
    assert cm.settings is not None
    monkeypatch.setattr(cm.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(cm.settings, "POLICY_FILE", temp_policy_file, raising=False)

    # Rewrite: foo -> bar
    post = cm.apply_post("answer with foo please", mode="default")
    assert post.action in {"allow", "rewrite"}
    if post.action == "rewrite":
        assert post.text is not None
        assert "bar" in post.text and "foo" not in post.text

    # Block: forbidden term
    post2 = cm.apply_post("this contains badword", mode="default")
    assert post2.action == "block"  # forbidden term triggers block
