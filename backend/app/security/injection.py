"""
Prompt injection detection and input/output validation.
"""
import re
from typing import Tuple

# Patterns commonly used in prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore (all |previous |above |prior )?instructions",
    r"disregard (your |the |all )?instructions",
    r"forget (everything|your instructions|what you were told)",
    r"you are now (a |an )?(?!helpful)",
    r"act as (?!a helpful)",
    r"new (persona|role|instructions|directive)",
    r"override (your |the |all )?(?:instructions|rules|guidelines)",
    r"pretend (you are|to be|that you)",
    r"simulate (being|a|an)",
    r"your new (instructions|directive|role|persona)",
    r"jailbreak",
    r"DAN mode",
    r"developer mode",
    r"bypass (all |your |the )?(?:restrictions|filters|guidelines)",
    r"<\s*(?:system|assistant|user)\s*>",  # XML-style prompt injection
    r"\[\s*(?:SYSTEM|INST|OVERRIDE)\s*\]",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

MAX_INPUT_LENGTH = 4000
MAX_OUTPUT_LENGTH = 8000


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Returns (is_injected, reason).
    """
    if len(text) > MAX_INPUT_LENGTH:
        return True, f"Input exceeds maximum length of {MAX_INPUT_LENGTH} characters"

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Potential prompt injection detected: '{match.group()}'"

    return False, ""


def validate_input(text: str) -> Tuple[bool, str]:
    """Basic input validation."""
    if not text or not text.strip():
        return False, "Input cannot be empty"
    if len(text) > MAX_INPUT_LENGTH:
        return False, f"Input too long (max {MAX_INPUT_LENGTH} chars)"
    return True, ""


def validate_output(text: str) -> Tuple[bool, str]:
    """Basic output validation to catch anomalies."""
    if not text:
        return False, "Empty response from LLM"
    if len(text) > MAX_OUTPUT_LENGTH:
        # Truncate rather than reject
        return True, ""
    return True, ""


def sanitize_for_log(text: str, max_len: int = 200) -> str:
    """Truncate and clean text for safe logging."""
    if not text:
        return ""
    return text[:max_len].replace("\n", " ") + ("..." if len(text) > max_len else "")
