from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re


SUPPORTED_SUFFIXES = {".md", ".txt"}
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*", re.IGNORECASE)


@dataclass(frozen=True)
class Chunk:
    source: str
    chunk_id: int
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class Citation:
    source: str
    chunk_id: int
    start_line: int
    end_line: int
    score: float
    excerpt: str


@dataclass(frozen=True)
class CitationPacket:
    question: str
    citations: list[Citation]

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "citations": [asdict(citation) for citation in self.citations],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [f"Question: {self.question}", ""]
        if not self.citations:
            lines.append("No matching source chunks found.")
            return "\n".join(lines)

        for index, citation in enumerate(self.citations, start=1):
            lines.append(f"{index}. {citation.source}:{citation.start_line}-{citation.end_line}")
            lines.append(f"Score: {citation.score:.2f}")
            lines.append(citation.excerpt)
            lines.append("")
        return "\n".join(lines).rstrip()


def load_corpus(root: Path | str, *, max_lines_per_chunk: int = 8) -> list[Chunk]:
    corpus_root = Path(root)
    if not corpus_root.exists():
        raise FileNotFoundError(f"Corpus directory does not exist: {corpus_root}")
    if max_lines_per_chunk < 1:
        raise ValueError("max_lines_per_chunk must be positive")

    chunks: list[Chunk] = []
    for path in sorted(p for p in corpus_root.rglob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES):
        chunks.extend(_chunk_file(path, corpus_root, max_lines_per_chunk=max_lines_per_chunk))
    return chunks


def build_citation_packet(question: str, chunks: list[Chunk], *, limit: int = 3) -> CitationPacket:
    if limit < 1:
        raise ValueError("limit must be positive")

    scored = [
        Citation(
            source=chunk.source,
            chunk_id=chunk.chunk_id,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            score=round(_score(question, chunk.text), 4),
            excerpt=_excerpt(chunk.text),
        )
        for chunk in chunks
    ]
    citations = [citation for citation in sorted(scored, key=lambda item: item.score, reverse=True) if citation.score > 0]
    return CitationPacket(question=question, citations=citations[:limit])


def _chunk_file(path: Path, root: Path, *, max_lines_per_chunk: int) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    current_start = 1

    for number, line in enumerate(lines, start=1):
        if not line.strip():
            if current:
                blocks.append((current_start, current))
                current = []
            current_start = number + 1
            continue
        if not current:
            current_start = number
        current.append(line)
        if len(current) >= max_lines_per_chunk:
            blocks.append((current_start, current))
            current = []
            current_start = number + 1

    if current:
        blocks.append((current_start, current))

    rel_source = path.relative_to(root).as_posix()
    return [
        Chunk(
            source=rel_source,
            chunk_id=index,
            start_line=start,
            end_line=start + len(block_lines) - 1,
            text="\n".join(block_lines).strip(),
        )
        for index, (start, block_lines) in enumerate(blocks, start=1)
        if "\n".join(block_lines).strip()
    ]


def _score(question: str, text: str) -> float:
    query_tokens = _tokens(question)
    if not query_tokens:
        return 0
    text_tokens = _tokens(text)
    if not text_tokens:
        return 0

    text_token_set = set(text_tokens)
    overlap = sum(1 for token in query_tokens if token in text_token_set)
    rare_boost = sum(1.5 for token in set(query_tokens) if len(token) >= 7 and token in text_token_set)
    phrase_boost = 2.0 if " ".join(query_tokens[:3]) and " ".join(query_tokens[:3]) in " ".join(text_tokens) else 0
    density = overlap / max(len(text_tokens), 1)
    return overlap + rare_boost + phrase_boost + density


def _tokens(value: str) -> list[str]:
    return [match.group(0).lower().strip("'") for match in TOKEN_RE.finditer(value)]


def _excerpt(text: str, *, max_chars: int = 360) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "..."
