"""Prompt templates for LLM-based label adjudication (Stage 4)."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert annotator trained in Theodor Adorno's Culture Industry theory.
Your task is to classify YouTube comments about popular music into critique categories.

You must be precise: only assign a label when the comment clearly expresses that
specific type of critique. Mere opinion ("this is bad") is NOT critique.
Fan reactions, lyric quoting, and generic praise/hate get NONE.

Categories:
1. STANDARDIZATION – Claims songs are formulaic, interchangeable, template-driven.
2. PSEUDO_INDIVIDUALIZATION – Superficial uniqueness masking sameness; branding over substance.
3. COMMODIFICATION_MARKET_LOGIC – Critique of charts, algorithms, labels, virality, streaming economics.
4. REGRESSIVE_LISTENING – Critique of passive, shallow, background consumption patterns.
5. AFFECTIVE_PREPACKAGING – Claims emotion is engineered, prefabricated, manipulative.
6. FORMAL_RESISTANCE – Recognition of genuine complexity, anti-formula, structural tension.
7. NONE – No meaningful critique present.

Rules:
- Multi-label is allowed (a comment can have multiple critique types).
- NONE must be true ONLY when ALL other labels are false.
- If sarcastic/ironic, note it and reduce certainty.
- Separate the commenter's own voice from quoted lyrics.
- "This slaps", "trash", "fire" alone → NONE.
"""

ADJUDICATION_PROMPT_TEMPLATE = """\
Classify the following YouTube comment. For each label, decide true/false and
extract the specific text evidence (quote the relevant span). If the comment is
in a language you can understand, analyze it. If not, set all labels to false
and note the language barrier.

Comment:
\"\"\"{comment}\"\"\"

Prior signals (from automated systems — use as hints, not gospel):
{prior_signals}

Respond with ONLY valid JSON matching this exact schema:
{{
  "labels": {{
    "STANDARDIZATION": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "PSEUDO_INDIVIDUALIZATION": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "COMMODIFICATION_MARKET_LOGIC": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "REGRESSIVE_LISTENING": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "AFFECTIVE_PREPACKAGING": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "FORMAL_RESISTANCE": {{"value": <bool>, "evidence": "<quoted span or empty string>"}},
    "NONE": {{"value": <bool>, "evidence": "<short reason or empty string>"}}
  }},
  "notes": "<1-2 sentence rationale>"
}}
"""

REPAIR_PROMPT = """\
Your previous response was not valid JSON. Please fix it.
The required schema is:
{{
  "labels": {{
    "STANDARDIZATION": {{"value": bool, "evidence": "..."}},
    "PSEUDO_INDIVIDUALIZATION": {{"value": bool, "evidence": "..."}},
    "COMMODIFICATION_MARKET_LOGIC": {{"value": bool, "evidence": "..."}},
    "REGRESSIVE_LISTENING": {{"value": bool, "evidence": "..."}},
    "AFFECTIVE_PREPACKAGING": {{"value": bool, "evidence": "..."}},
    "FORMAL_RESISTANCE": {{"value": bool, "evidence": "..."}},
    "NONE": {{"value": bool, "evidence": "..."}}
  }},
  "notes": "short rationale"
}}

Your previous (invalid) response was:
{previous_response}

Please output ONLY the corrected JSON, nothing else.
"""


def format_adjudication_prompt(
    comment: str,
    rule_hits: dict[str, bool] | None = None,
    embedding_scores: dict[str, float] | None = None,
) -> str:
    """Format the adjudication prompt with prior signals."""
    signals_parts = []
    if rule_hits:
        triggered = [k for k, v in rule_hits.items() if v]
        signals_parts.append(f"Rule-based hits: {triggered if triggered else 'none'}")
    if embedding_scores:
        top = sorted(embedding_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        signals_parts.append(
            "Top embedding similarities: "
            + ", ".join(f"{k}={v:.2f}" for k, v in top)
        )
    prior_signals = "\n".join(signals_parts) if signals_parts else "No prior signals."

    return ADJUDICATION_PROMPT_TEMPLATE.format(
        comment=comment, prior_signals=prior_signals
    )
