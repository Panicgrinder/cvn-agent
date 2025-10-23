from __future__ import annotations

import os
import tempfile

from utils.context_notes import load_context_notes


def write(p: str, txt: str) -> None:
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)


def test_directory_order_with_ORDER_file():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "context.notes")
        os.makedirs(d, exist_ok=True)

        # Files a, b, c
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        c = os.path.join(d, "c.txt")
        write(a, "A")
        write(b, "B")
        write(c, "C")

        # Enforce order: b, a (c should come last alphabetically)
        order = os.path.join(d, "ORDER.txt")
        write(order, "b.txt\na.txt\n")

        res = load_context_notes([d], max_chars=100)
        assert res is not None
        # Expect: B, then A, then C
        assert res.replace("\n", " ").startswith("B")
        # naive order check: positions
        pos_b = res.find("B")
        pos_a = res.find("A")
        pos_c = res.find("C")
        assert 0 <= pos_b < pos_a < pos_c


def test_directory_order_default_alphabetical():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "context.notes")
        os.makedirs(d, exist_ok=True)

        a = os.path.join(d, "a.txt")
        c = os.path.join(d, "c.txt")
        b = os.path.join(d, "b.txt")
        write(a, "A")
        write(c, "C")
        write(b, "B")

        # No ORDER file -> alphabetical a, b, c
        res = load_context_notes([d], max_chars=100)
        assert res is not None
        pos_a = res.find("A")
        pos_b = res.find("B")
        pos_c = res.find("C")
        assert 0 <= pos_a < pos_b < pos_c


def test_ignore_meta_files_and_normalize():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "context.notes")
        os.makedirs(d, exist_ok=True)

        # Meta files (should be ignored)
        with open(os.path.join(d, "ORDER.txt"), "w", encoding="utf-8") as f:
            f.write("b.txt\n")
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Readme\n")

        # Content files
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        with open(a, "w", encoding="utf-8") as f:
            f.write("A\n\n\n\nA2\n")
        with open(b, "w", encoding="utf-8") as f:
            f.write("B\n")

        res = load_context_notes([d], max_chars=200)
        assert res is not None
        # Readme content must not appear
        assert "Readme" not in res
        # ORDER file content must not appear either
        assert "b.txt" not in res
        # Normalization: more than two blank lines collapsed
        assert "A\n\nA2" in res
