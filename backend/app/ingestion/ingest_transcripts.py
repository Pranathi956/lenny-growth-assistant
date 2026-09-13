"""
Standalone ingestion script.

Usage:
    python -m app.ingestion.ingest_transcripts

Drops any .txt file into backend/data/transcripts/ and the RAG index (see
agent/rag.py) will pick it up on next app startup, or immediately if you
call this script, which just validates the directory and reports counts --
the actual indexing is lazy (TF-IDF is cheap enough to build in-memory on
startup, so there's no separate "build" step required for the demo).

For a real deployment with a large transcript archive, swap this for a
scheduled job that: downloads new transcripts from the source repo,
writes them to transcripts_dir, and calls agent.rag.get_index(...).load()
to refresh the in-memory index without restarting the app.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import settings
from app.agent.rag import get_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lenny.ingest")


def main():
    if not os.path.isdir(settings.transcripts_dir):
        logger.error(f"Transcripts directory not found: {settings.transcripts_dir}")
        sys.exit(1)

    index = get_index(settings.transcripts_dir)
    index.load()
    logger.info(f"Indexed {len(index.chunks)} chunks.")
    if len(index.chunks) == 0:
        logger.warning(
            "No transcripts found. Add .txt files to data/transcripts/ "
            "(one file per episode, filename becomes the title)."
        )


if __name__ == "__main__":
    main()
