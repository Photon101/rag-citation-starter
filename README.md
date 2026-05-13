# RAG Citation Starter

Small, dependency-light starter for grounded document retrieval. It ingests local text or Markdown files, chunks them with line-range metadata, scores chunks against a question, and emits a citation packet that can be handed to an LLM or used directly in review workflows.

This is intentionally not a chatbot shell. It is the reliable retrieval layer underneath one: clear sources, deterministic scoring, and JSON output that makes hallucination checks easier.

## Features

- Reads `.txt` and `.md` files from a corpus directory.
- Keeps source file, chunk id, and start/end line citations.
- Uses simple lexical scoring with phrase and token overlap boosts.
- Emits Markdown or JSON citation packets.
- Has tests and a no-network example.

## Quick Start

```bash
PYTHONPATH=src python3 -m rag_citation_starter.cli examples/corpus "How does escalation work?"
```

JSON output:

```bash
PYTHONPATH=src python3 -m rag_citation_starter.cli examples/corpus "How does escalation work?" --json
```

Run tests:

```bash
uv run --extra dev python -m pytest
```

## Example Output

```text
Question: How does escalation work?

1. examples/corpus/support_policy.md:7-10
Score: 8.75
Escalation is required when a support request includes legal risk...
```

## Good Fit

- FAQ and support-document assistants.
- Internal knowledge-base search.
- Scientific or policy document review queues.
- Pre-LLM citation retrieval where every answer needs a source.

## Not Included

- No paid LLM calls.
- No vector database.
- No private document storage.

Those can be added after the retrieval behavior is understood and tested.
