from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from utils.rag import build_index, retrieve, save_index, load_index


@pytest.mark.unit
def test_retrieve_ranking_and_top_k(tmp_path: Path) -> None:
    # Zwei einfache Textdateien erstellen
    p1 = tmp_path / "doc1.txt"
    p2 = tmp_path / "doc2.txt"
    p1.write_text("alpha beta beta", encoding="utf-8")
    p2.write_text("gamma delta alpha", encoding="utf-8")

    # Index aufbauen
    idx = build_index([str(p1), str(p2)])

    # Query mit eindeutigem Signal für doc1
    hits = retrieve(idx, "beta", top_k=1)
    assert isinstance(hits, list)
    assert len(hits) == 1
    h0 = hits[0]
    assert isinstance(h0.get("score"), str)
    # Score sollte > 0 sein, wenn es einen Treffer gibt
    assert float(h0.get("score", "0")) > 0.0
    # Quelle sollte doc1 enthalten
    assert str(p1) in h0.get("source", "")

    # Top-K = 2 sollte beide Dokumente enthalten (alpha ist geteilt; beta ist spezifischer)
    hits2 = retrieve(idx, "alpha", top_k=2)
    assert len(hits2) == 2
    sources2: List[str] = [h.get("source", "") for h in hits2]
    assert str(p1) in sources2 and str(p2) in sources2


@pytest.mark.unit
def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    p1 = tmp_path / "doc1.txt"
    p2 = tmp_path / "doc2.txt"
    p1.write_text("alpha beta", encoding="utf-8")
    p2.write_text("alpha", encoding="utf-8")

    idx = build_index([str(p1), str(p2)])
    out = tmp_path / "index.json"
    save_index(idx, str(out))

    idx2 = load_index(str(out))
    assert idx2 is not None
    assert idx2.n_docs == 2
    # Grundbegriffe sollten im DF vorkommen
    assert "alpha" in idx2.df
    # retrieve sollte weiterhin sinnvolle Ergebnisse liefern
    hits = retrieve(idx2, "alpha", top_k=1)
    assert hits and float(hits[0].get("score", "0")) > 0.0
