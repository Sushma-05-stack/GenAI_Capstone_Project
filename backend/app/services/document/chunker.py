"""
Text chunking with overlapping windows.
"""
import re
from typing import List
from dataclasses import dataclass


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    token_estimate: int


def clean_text(text: str) -> str:
    """Basic text cleaning - normalize whitespace, remove control chars."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r" {3,}", "  ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[TextChunk]:
    """
    Split text into chunks by word count with overlap.
    Returns list of TextChunk objects.
    """
    text = clean_text(text)
    words = text.split()
    chunks = []
    i = 0
    char_pos = 0

    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk_words = words[i:end]
        content = " ".join(chunk_words)
        token_estimate = int(len(content) / 4)  # rough 4 chars/token estimate

        chunks.append(
            TextChunk(
                content=content,
                chunk_index=len(chunks),
                start_char=char_pos,
                end_char=char_pos + len(content),
                token_estimate=token_estimate,
            )
        )
        char_pos += len(content) - len(" ".join(words[max(0, end - chunk_overlap):end]))
        i = end - chunk_overlap if end < len(words) else end

    return chunks
