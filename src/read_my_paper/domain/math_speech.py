"""Spoken-English rendering for Unicode math that survives PDF text extraction."""

from __future__ import annotations

import re
import unicodedata


SYMBOL_WORDS = {
    # Arithmetic and products
    "×": " times ",
    "·": " times ",
    "⋅": " times ",
    "∗": " star ",
    "⊙": " element-wise times ",
    "⊗": " tensor product ",
    "⊕": " circle plus ",
    "∘": " composed with ",
    "÷": " divided by ",
    "⁄": " over ",
    "∕": " over ",
    "±": " plus or minus ",
    "∓": " minus or plus ",
    "−": " minus ",
    # Relations
    "≠": " is not equal to ",
    "≈": " is approximately ",
    "≃": " is approximately ",
    "≅": " is approximately ",
    "∼": " is distributed as ",
    "≡": " is equivalent to ",
    "∝": " is proportional to ",
    "≤": " is less than or equal to ",
    "≥": " is greater than or equal to ",
    "≪": " is much less than ",
    "≫": " is much greater than ",
    "≔": " is defined as ",
    "≜": " is defined as ",
    # Sets and logic
    "∈": " in ",
    "∉": " not in ",
    "∋": " contains ",
    "⊂": " subset of ",
    "⊆": " subset of or equal to ",
    "⊃": " superset of ",
    "⊇": " superset of or equal to ",
    "∪": " union ",
    "∩": " intersect ",
    "∖": " minus ",
    "∅": " the empty set ",
    "∀": " for all ",
    "∃": " there exists ",
    "¬": " not ",
    "∧": " and ",
    "∨": " or ",
    "⊤": " transpose ",
    "⊥": " is perpendicular to ",
    # Arrows
    "→": " to ",
    "⟶": " to ",
    "←": " gets ",
    "↦": " maps to ",
    "⇒": " implies ",
    "⟹": " implies ",
    "⇔": " if and only if ",
    "⟺": " if and only if ",
    "↑": " up ",
    "↓": " down ",
    # Calculus, sums, and norms
    "∂": " partial ",
    "∇": " gradient ",
    "∆": " delta ",
    "∫": " integral ",
    "∮": " contour integral ",
    "∑": " sum ",
    "∏": " product ",
    "√": " square root of ",
    "∛": " cube root of ",
    "∞": " infinity ",
    "′": " prime ",
    "″": " double prime ",
    "‖": " norm ",
    "∥": " parallel to ",
    "∣": " given ",
    "⟨": " the inner product of ",
    "⟩": " ",
    "⌊": " floor of ",
    "⌋": " ",
    "⌈": " ceiling of ",
    "⌉": " ",
    "⋯": " dot dot dot ",
    "⋮": " dot dot dot ",
    "⋱": " dot dot dot ",
    "°": " degrees ",
}

SUPERSCRIPTS = dict(zip(
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷʸᶻᵀˣ",
    "0123456789+-=()abcdefghijklmnoprstuvwyzT×",
))
SUBSCRIPTS = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜᵢⱼ", "0123456789+-=()aeoxhklmnpstij"))
SUBSCRIPT = "subscript"
SUPERSCRIPT = "superscript"
SPOKEN_POWERS = {"2": "squared", "3": "cubed", "-1": "inverse", "T": "transpose"}

# Accents that follow their letter (x̂) and spacing forms OCR tends to place before it (ˆx).
COMBINING_ACCENTS = {"\u0302": "hat", "\u0303": "tilde", "\u0304": "bar", "\u0305": "bar",
                     "\u0307": "dot", "\u0308": "double dot", "\u20d7": "vector"}
SPACING_ACCENTS = {"ˆ": "hat", "˜": "tilde", "¯": "bar", "˙": "dot", "¨": "double dot"}

GREEK_NAME_NOISE = {"GREEK", "SMALL", "CAPITAL", "LETTER", "SYMBOL", "LUNATE", "FINAL"}


def _run_pattern(characters: dict[str, str]) -> re.Pattern[str]:
    return re.compile(f"[{re.escape(''.join(characters))}]+")


SUPERSCRIPT_RUN = _run_pattern(SUPERSCRIPTS)
SUBSCRIPT_RUN = _run_pattern(SUBSCRIPTS)
COMBINING_ACCENT = re.compile(f"(\\w)([{''.join(COMBINING_ACCENTS)}])")
SPACING_ACCENT = re.compile(f"([{re.escape(''.join(SPACING_ACCENTS))}])\\s*(\\w)")
_PARTIAL_TERM = r"(\w+(?:\s*\([^()]*\))?)"  # E, a, or f (yi)
PARTIAL_PAIR = re.compile(rf"∂\s*{_PARTIAL_TERM}\s+∂\s*{_PARTIAL_TERM}")
NORM = re.compile(r"[‖∥]\s*([^‖∥]{1,30}?)\s*[‖∥]")  # ‖w‖ / ∥w∥; a lone ∥ still reads "parallel to"


def unicode_to_speech(text: str) -> str:
    """Replace math symbols with words; spacing is left loose for the caller to normalize."""
    text = _rewrite_constructs(text)
    text = unicodedata.normalize("NFKC", text)
    return "".join(_spoken_character(character) for character in text)


def _rewrite_constructs(text: str) -> str:
    """Handle multi-character forms before NFKC flattens them (x² would become x2)."""
    # Negation overlays: OCR emits "̸=" for ≠ and "̸∈" for ∉.
    text = re.sub(r"\u0338\s*=|=\s*\u0338", "≠", text)
    text = re.sub(r"\u0338\s*∈|∈\s*\u0338", "∉", text)
    text = text.replace("\u0338", "")

    # The PDF text layer flattens ∂E/∂a into "∂E ∂a"; two adjacent partials are almost always a derivative.
    text = PARTIAL_PAIR.sub(
        lambda match: f" the partial derivative of {match.group(1)} with respect to {match.group(2)} ", text
    )

    text = COMBINING_ACCENT.sub(lambda match: f" {match.group(1)} {COMBINING_ACCENTS[match.group(2)]} ", text)
    text = SPACING_ACCENT.sub(lambda match: f" {match.group(2)} {SPACING_ACCENTS[match.group(1)]} ", text)

    text = NORM.sub(lambda match: f" the norm of {match.group(1)} ", text)

    text = SUPERSCRIPT_RUN.sub(lambda match: f" {_spoken_power(match.group())} ", text)
    text = SUBSCRIPT_RUN.sub(
        lambda match: f" {SUBSCRIPT} {''.join(SUBSCRIPTS[c] for c in match.group())} ", text
    )

    # Context-dependent readings: "3×3 conv" and "∼2x faster".
    text = re.sub(r"(?<=\d)\s*×\s*(?=\d)", " by ", text)
    text = re.sub(r"∼\s*(?=\d)", " roughly ", text)

    # Plain ASCII relations, only when spaced like an equation.
    text = text.replace(":=", " is defined as ")
    text = re.sub(r"(?<=\s)=(?=\s)", "equals", text)
    text = re.sub(r"(?<=\s)<(?=\s)", "is less than", text)
    text = re.sub(r"(?<=\s)>(?=\s)", "is greater than", text)
    return text


def _spoken_power(superscript: str) -> str:
    power = "".join(SUPERSCRIPTS[character] for character in superscript)
    return SPOKEN_POWERS.get(power, f"to the {power}").replace("×", " by ")  # ℝⁿˣⁿ -> R to the n by n


def _spoken_character(character: str) -> str:
    if character in SYMBOL_WORDS:
        return SYMBOL_WORDS[character]
    if character.isascii():
        return character

    name = unicodedata.name(character, "")
    if name.startswith("GREEK"):
        letter = " ".join(word for word in name.split() if word not in GREEK_NAME_NOISE).casefold()
        return f" {letter.replace('lamda', 'lambda')} "
    if unicodedata.category(character) == "Sm":
        return f" {name.casefold()} "
    return character
