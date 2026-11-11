from __future__ import annotations

import re
from typing import Literal, cast

from pydantic import BaseModel, Field

from app.services.extraction.labels import CANONICAL_LABELS, normalize_label
from app.services.extraction.text_utils import fold

_FUNCTIONAL_WORDS = {
    "pt": (
        "nao",
        "uma",
        "dos",
        "das",
        "pelo",
        "pela",
        "mes",
        "ano",
        "empregador",
        "empregado",
        "proventos",
        "descontos",
        "liquido",
        "salario",
        "agencia",
        "codigo",
        "funcao",
        "banco",
        "pagamento",
    ),
    "es": (
        "los",
        "las",
        "del",
        "una",
        "mes",
        "ano",
        "empleador",
        "empleado",
        "haberes",
        "descuentos",
        "neto",
        "salario",
        "agencia",
        "codigo",
        "puesto",
        "banco",
        "pago",
    ),
    "en": (
        "the",
        "of",
        "and",
        "with",
        "month",
        "year",
        "employer",
        "employee",
        "earnings",
        "deductions",
        "net",
        "salary",
        "agency",
        "code",
        "position",
        "bank",
        "payment",
    ),
}


LanguageCode = Literal["pt", "es", "en"]


class LanguageGuess(BaseModel):
    lang: LanguageCode
    scores: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


def _alias_pattern(alias: str) -> re.Pattern[str] | None:
    normalized = normalize_label(alias)
    if not normalized:
        return None
    tokens = normalized.split()
    body = r"[\W_]*".join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<!\w){body}(?!\w)")


_ALIAS_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "pt": [],
    "es": [],
    "en": [],
}
for _canonical, _by_language in CANONICAL_LABELS.items():
    for _lang, _aliases in _by_language.items():
        for _alias in _aliases:
            _pattern = _alias_pattern(_alias)
            if _pattern is not None:
                _ALIAS_PATTERNS[_lang].append(_pattern)

_WORD_PATTERNS = {
    lang: [
        re.compile(rf"(?<!\w){re.escape(word)}(?!\w)")
        for word in words
    ]
    for lang, words in _FUNCTIONAL_WORDS.items()
}


def detect_language(text: str) -> LanguageGuess:
    folded = fold(text)
    scores = {"pt": 0.0, "es": 0.0, "en": 0.0}

    for lang, patterns in _ALIAS_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(folded):
                scores[lang] += 2.0

    for lang, patterns in _WORD_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(folded):
                scores[lang] += 1.0

    total = sum(scores.values())
    top_lang = max(
        scores,
        key=lambda lang: (scores[lang], {"pt": 3, "es": 2, "en": 1}[lang]),
    )
    top_score = scores[top_lang]

    if total == 0:
        return LanguageGuess(
            lang="pt",
            scores=scores,
            confidence=0.0,
        )

    confidence = round(top_score / total, 4)
    if top_score < 2.0:
        return LanguageGuess(
            lang="pt",
            scores=scores,
            confidence=min(confidence, 0.3),
        )

    return LanguageGuess(
        lang=cast(LanguageCode, top_lang),
        scores=scores,
        confidence=confidence,
    )
