from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

import pytest

from scripts.dependency_check import coerce_json_to_jsonl


@pytest.mark.scripts
@pytest.mark.unit
def test_coerce_json_to_jsonl_parses_array_and_object() -> None:
    arr = json.dumps([{"a": 1}, {"b": 2}])
    obj = json.dumps({"k": "v"})
    out_arr = coerce_json_to_jsonl(arr)
    out_obj = coerce_json_to_jsonl(obj)
    assert isinstance(out_arr, list) and len(out_arr) == 2 and out_arr[0]["a"] == 1
    assert isinstance(out_obj, list) and len(out_obj) == 1 and out_obj[0]["k"] == "v"


@pytest.mark.scripts
@pytest.mark.unit
def test_coerce_json_to_jsonl_handles_jsonl_and_garbage() -> None:
    text = "\n".join(["{\"x\": 1}", "not-json", " { \"y\" : 2 } ", "", "{\"z\":3}"])
    out = coerce_json_to_jsonl(text)
    assert [d.get("x") for d in out if "x" in d] == [1]
    assert [d.get("y") for d in out if "y" in d] == [2]
    assert [d.get("z") for d in out if "z" in d] == [3]
