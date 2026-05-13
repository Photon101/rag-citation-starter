from __future__ import annotations

import argparse
from pathlib import Path

from .retrieval import build_citation_packet, load_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-cited retrieval packet from a local corpus.")
    parser.add_argument("corpus", type=Path, help="Directory containing .txt or .md files")
    parser.add_argument("question", help="Question or search prompt")
    parser.add_argument("--limit", type=int, default=3, help="Maximum cited chunks to return")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args()

    chunks = load_corpus(args.corpus)
    packet = build_citation_packet(args.question, chunks, limit=args.limit)
    print(packet.to_json() if args.json else packet.to_markdown())


if __name__ == "__main__":
    main()
