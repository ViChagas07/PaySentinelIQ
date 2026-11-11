from __future__ import annotations

import re
import unicodedata

_CONFUSIONS = {
    "O": "0",
    "o": "0",
    "l": "1",
    "I": "1",
    "S": "5",
    "B": "8",
}
_CONFUSION_RUN = re.compile(r"[0-9OoIlSB]+")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [
        re.sub(r"[ \t\f\v]+", " ", line).strip()
        for line in normalized.split("\n")
    ]
    return "\n".join(lines).strip()


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", normalize_text(text))
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return without_marks.lower()


def fix_digit_confusions(token: str) -> tuple[str, list[str]]:
    corrections: list[str] = []

    def replace(match: re.Match[str]) -> str:
        sequence = match.group(0)
        digits = sum(char.isdigit() for char in sequence)
        letters = len(sequence) - digits
        if digits == 0 or letters == 0 or digits < letters:
            return sequence

        result: list[str] = []
        for offset, char in enumerate(sequence, start=match.start()):
            replacement = _CONFUSIONS.get(char, char)
            if replacement != char:
                corrections.append(f"{char}->{replacement}@{offset}")
            result.append(replacement)
        return "".join(result)

    return _CONFUSION_RUN.sub(replace, token), corrections
