from pathlib import Path

from rag_citation_starter import build_citation_packet, load_corpus


def test_load_corpus_tracks_source_and_line_ranges(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "notes.md").write_text("Alpha line\nBeta line\n\nGamma line\n", encoding="utf-8")

    chunks = load_corpus(corpus)

    assert [(chunk.source, chunk.start_line, chunk.end_line, chunk.text) for chunk in chunks] == [
        ("notes.md", 1, 2, "Alpha line\nBeta line"),
        ("notes.md", 4, 4, "Gamma line"),
    ]


def test_build_citation_packet_prefers_relevant_chunk(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "support.md").write_text(
        "Routine cases use normal docs.\n\nSecurity incidents require escalation and legal review.\n",
        encoding="utf-8",
    )

    packet = build_citation_packet("When do security incidents escalate?", load_corpus(corpus), limit=1)

    assert packet.citations
    assert packet.citations[0].source == "support.md"
    assert packet.citations[0].start_line == 3
    assert "Security incidents require escalation" in packet.citations[0].excerpt


def test_packet_can_emit_json() -> None:
    packet = build_citation_packet(
        "billing invoice",
        [
            type("ChunkLike", (), {
                "source": "faq.txt",
                "chunk_id": 1,
                "start_line": 1,
                "end_line": 1,
                "text": "Billing invoice requests need account ids.",
            })()
        ],
    )

    output = packet.to_json()

    assert '"question": "billing invoice"' in output
    assert '"source": "faq.txt"' in output


def test_empty_question_returns_no_citations(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "notes.txt").write_text("One useful source line.", encoding="utf-8")

    packet = build_citation_packet("", load_corpus(corpus))

    assert packet.citations == []
    assert "No matching source chunks found" in packet.to_markdown()
