"""
Lightweight retrieval layer over Lenny's Podcast transcripts.

Design choice (documented in architecture.md): we use TF-IDF + cosine
similarity instead of a neural embedding model. This keeps the system
dependency-light and fully offline-capable for the local-model demo
(no calls out to an embeddings API, no large model download). It is
swappable for pgvector + a real embedding model later — see
architecture.md "Future improvements".
"""
import os
import re
import glob
import logging
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("lenny.rag")


@dataclass
class Chunk:
    chunk_id: str
    transcript_id: str
    title: str
    text: str


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Word-based sliding window chunking. Simple and predictable, which
    matters more here than being maximally clever — the evaluator needs
    to be able to trace an answer back to an exact chunk of source text."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks or [text]


class TranscriptIndex:
    """In-memory TF-IDF index built at startup from .txt files in transcripts_dir.

    Each transcript file's name becomes its title. Rebuild is triggered by
    calling .load() again (e.g. from an admin endpoint), which re-reads the
    directory — this is the "refresh" mechanism referenced in the PRD.
    """

    def __init__(self, transcripts_dir: str):
        self.transcripts_dir = transcripts_dir
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.load()

    def load(self):
        self.chunks = []
        paths = sorted(glob.glob(os.path.join(self.transcripts_dir, "*.txt")))
        for path in paths:
            title = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            for i, piece in enumerate(_chunk_text(raw)):
                self.chunks.append(
                    Chunk(
                        chunk_id=f"{title}::chunk{i}",
                        transcript_id=title,
                        title=title,
                        text=piece,
                    )
                )
        if self.chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
            self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])
        else:
            self.vectorizer = None
            self.matrix = None
        logger.info(f"Indexed {len(self.chunks)} chunks from {len(paths)} transcripts")

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        if not self.chunks or self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]
        return [(self.chunks[i], float(sims[i])) for i in ranked if sims[i] > 0.0]


_index: TranscriptIndex | None = None


def get_index(transcripts_dir: str) -> TranscriptIndex:
    global _index
    if _index is None:
        _index = TranscriptIndex(transcripts_dir)
    return _index
