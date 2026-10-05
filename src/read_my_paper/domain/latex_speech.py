"""Spoken-English rendering for LaTeX, including Docling's token-spaced formula output."""

from __future__ import annotations

import re

from read_my_paper.domain.math_speech import SUBSCRIPT, SUPERSCRIPT, unicode_to_speech


TOKEN_PATTERN = re.compile(r"\\[A-Za-z]+\*?|\\.|\d+(?:\.\d+)?|[A-Za-z]|\S")
# Equation numbers such as "(6)" or Docling's "\quad ( 1 0 )".
EQUATION_NUMBER = re.compile(r"(?:\\q?quad\s*)+\(\s*(?:\d\s*)+\)|\(\s*(?:\d\s*)+\)\s*\.?\s*$")

GREEK = {
    name: name.removeprefix("var").casefold()
    for name in (
        "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta", "theta", "vartheta",
        "iota", "kappa", "lambda", "mu", "nu", "xi", "pi", "varpi", "rho", "varrho", "sigma", "varsigma",
        "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda",
        "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
    )
}

SYMBOLS = {
    "cdot": "times", "times": "times", "ast": "star", "star": "star", "circ": "composed with",
    "odot": "element-wise times", "otimes": "tensor product", "oplus": "circle plus",
    "pm": "plus or minus", "mp": "minus or plus", "div": "divided by",
    "neq": "is not equal to", "ne": "is not equal to", "approx": "is approximately",
    "simeq": "is approximately", "sim": "is distributed as", "equiv": "is equivalent to",
    "propto": "is proportional to", "leq": "is less than or equal to", "le": "is less than or equal to",
    "geq": "is greater than or equal to", "ge": "is greater than or equal to",
    "ll": "is much less than", "gg": "is much greater than",
    "triangleq": "is defined as", "coloneqq": "is defined as",
    "in": "in", "notin": "not in", "subset": "subset of", "subseteq": "subset of or equal to",
    "cup": "union", "cap": "intersect", "setminus": "minus", "emptyset": "the empty set",
    "forall": "for all", "exists": "there exists", "neg": "not", "land": "and", "lor": "or",
    "to": "to", "rightarrow": "to", "leftarrow": "gets", "mapsto": "maps to",
    "Rightarrow": "implies", "implies": "implies", "iff": "if and only if", "Leftrightarrow": "if and only if",
    "infty": "infinity", "partial": "partial", "prime": "prime", "top": "transpose", "intercal": "transpose",
    "perp": "is perpendicular to", "mid": "given", "parallel": "parallel to", "ell": "l",
    "ldots": "dot dot dot", "cdots": "dot dot dot", "dots": "dot dot dot", "vdots": "dot dot dot",
    "ddots": "dot dot dot", "langle": "the inner product of", "lfloor": "the floor of",
    "lceil": "the ceiling of", "Vert": "norm", "lVert": "the norm of", "colon": ":",
}

# Plain characters; operators speak as words, brackets vanish in the final tidy step.
CHARACTERS = {
    "=": "equals", "+": "plus", "-": "minus", "<": "is less than", ">": "is greater than",
    "*": "star", "/": "over", "|": "given", "!": "factorial", "'": "prime", ";": ",", "&": "", "}": "",
}
ESCAPED = {"\\": ",", "%": "percent", "&": "and"}
SILENT = {
    "left", "right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "displaystyle", "textstyle", "scriptstyle", "limits", "nolimits", "quad", "qquad", "nonumber",
    "notag", "rangle", "rfloor", "rceil", "rVert", "lvert", "rvert",
}

FUNCTIONS = {
    "Var": "the variance of", "Cov": "the covariance of", "std": "the standard deviation of",
    "log": "the log of", "ln": "the natural log of", "exp": "the exponential of",
    "max": "the max of", "min": "the min of", "argmax": "the arg max of", "argmin": "the arg min of",
    "sup": "the supremum of", "inf": "the infimum of", "softmax": "the softmax of",
    "sigmoid": "the sigmoid of", "tanh": "tanh of", "sin": "sine of", "cos": "cosine of",
    "det": "the determinant of", "diag": "the diagonal of", "sign": "the sign of", "rank": "the rank of",
    "tr": "the trace of", "Pr": "the probability of", "KL": "the KL divergence of",
    "ReLU": "ReLU of", "PReLU": "PReLU of",
}
# Single letters only read as functions when an argument bracket follows: f(x), E[x].
LETTER_FUNCTIONS = {
    "E": ("the expectation of", "["), "P": ("the probability of", "(["),
    "f": ("f of", "("), "g": ("g of", "("), "h": ("h of", "("), "p": ("p of", "("), "q": ("q of", "("),
}
# Spaced letter runs ("V a r") are joined only into words this long, to avoid false matches.
MIN_SPELLED_FUNCTION = 3

BIG_OPERATORS = {
    "sum": "the sum", "prod": "the product", "int": "the integral", "oint": "the contour integral",
    "bigcup": "the union", "bigcap": "the intersection",
}
ACCENTS = {
    "hat": "hat", "widehat": "hat", "bar": "bar", "overline": "bar", "tilde": "tilde",
    "widetilde": "tilde", "vec": "vector", "dot": "dot", "ddot": "double dot",
}
TEXT_FONTS = {"mathrm", "operatorname", "text", "textrm", "textit", "textbf", "mbox"}
MATH_FONTS = {"mathcal", "mathbf", "mathit", "mathsf", "mathtt", "mathbb", "mathfrak", "boldsymbol", "bm"}
MATRIX_ENVIRONMENTS = {"matrix", "pmatrix", "bmatrix", "vmatrix", "Bmatrix"}

BRACKETS = {"(": ")", "[": "]"}
POWERS = {
    ("2",): "squared", ("3",): "cubed", ("T",): "transpose", ("transpose",): "transpose",
    ("minus", "1"): "inverse", ("prime",): "prime", ("star",): "star",
}
FRACTIONS = {("1", "2"): "one half", ("1", "3"): "one third", ("1", "4"): "one quarter"}
IS_SET_TO = "is set to"

# Adjacent products get an explicit "times": fractions and function applications after terms.
PRODUCT_KINDS = {"fraction", "apply"}
TERM_KINDS = PRODUCT_KINDS | {"term"}


def latex_to_speech(latex: str) -> str:
    """Render LaTeX as spoken English, e.g. "the partial derivative of E with respect to a"."""
    text = EQUATION_NUMBER.sub("", latex.strip().strip("$"))
    if not text:
        return ""

    words = _Parser(TOKEN_PATTERN.findall(text)).parse()
    return _tidy(" ".join(words))


def _tidy(text: str) -> str:
    text = re.sub(r"[()\[\]{}]", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,;])(?:\s*[,;])+", r"\1", text)
    text = re.sub(r"\s+", " ", unicode_to_speech(text))
    return text.strip(" ,;")


def _fraction(numerator: list[str], denominator: list[str]) -> list[str]:
    for symbol, derivative in (("partial", "the partial derivative"), ("d", "the derivative")):
        if numerator[:1] == [symbol] and denominator[:1] == [symbol] and len(denominator) > 1:
            target, variable = numerator[1:], denominator[1:]
            if not target:
                return [f"{derivative} with respect to", *variable, "of"]
            return [f"{derivative} of", *target, "with respect to", *variable]

    if spoken := FRACTIONS.get((" ".join(numerator), " ".join(denominator))):
        return [spoken]
    return [*numerator, "over", *denominator]


def _power(exponent: list[str]) -> list[str]:
    if spoken := POWERS.get(tuple(exponent)):
        return [spoken]
    # x^{(l)} is a layer or sample index in ML papers, not an exponent.
    if exponent[:1] == ["("] and exponent[-1:] == [")"]:
        return [SUPERSCRIPT, *exponent]
    return ["to the power of", *exponent]


def _split_spelled_functions(letters: list[str]) -> list[str]:
    """Join Docling's spaced letters back into known function names: V a r -> Var."""
    pieces: list[str] = []
    index = 0

    while index < len(letters):
        for length in range(len(letters) - index, MIN_SPELLED_FUNCTION - 1, -1):
            word = "".join(letters[index : index + length])
            if word in FUNCTIONS:
                pieces.append(word)
                index += length
                break
        else:
            pieces.append(letters[index])
            index += 1

    return pieces


class _Parser:
    """Recursive-descent reader that turns LaTeX tokens into spoken words."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> list[str]:
        return self._sequence(set())

    # Token stream helpers

    def _peek(self, ahead: int = 0) -> str | None:
        index = self.position + ahead
        return self.tokens[index] if index < len(self.tokens) else None

    def _next(self) -> str:
        token = self.tokens[self.position]
        self.position += 1
        return token

    def _skip(self, token: str) -> None:
        if self._peek() == token:
            self._next()

    # Grammar

    def _sequence(self, stop: set[str]) -> list[str]:
        words: list[str] = []
        previous_kind: str | None = None

        while (token := self._peek()) is not None and token not in stop:
            kind, atom = self._atom()
            if not atom:
                continue

            if kind in PRODUCT_KINDS and previous_kind in TERM_KINDS:
                words.append("times")
            words += atom + self._scripts()
            previous_kind = kind

        return words

    def _scripts(self) -> list[str]:
        words: list[str] = []

        while (token := self._peek()) in ("^", "_", "'"):
            self._next()
            if token == "'":
                words.append("prime")
            elif token == "_":
                words += [SUBSCRIPT, *self._argument()]
            else:
                words += _power(self._argument())

        return words

    def _argument(self) -> list[str]:
        """A braced group or exactly one token, as in x_i or \\frac12."""
        token = self._peek()
        if token is None:
            return []
        if token == "{":
            return self._group()
        if token.startswith("\\"):
            return self._atom()[1]

        self._next()
        word = CHARACTERS.get(token, token)
        return [word] if word else []

    def _group(self) -> list[str]:
        self._next()
        words = self._sequence({"}"})
        self._skip("}")
        return words

    def _raw_group(self) -> str:
        if self._peek() != "{":
            return ""

        self._next()
        parts: list[str] = []
        while self._peek() not in (None, "}"):
            parts.append(self._next())
        self._skip("}")
        return "".join(parts)

    def _atom(self) -> tuple[str, list[str]]:
        token = self._next()

        if token == "{":
            self.position -= 1
            return "term", self._group()
        if token.startswith("\\"):
            return self._command(token[1:])
        if token.isalpha():
            return self._letters(token)
        if token[0].isdigit():
            return "term", [self._number(token)]
        if token == ":" and self._peek() == "=":
            self._next()
            return "operator", [IS_SET_TO]

        word = CHARACTERS.get(token, token)
        return "operator", [word] if word else []

    def _number(self, first: str) -> str:
        """Docling spaces digits apart ("0 . 0 1"); join them back into one number."""
        digits = [first]
        while (token := self._peek()) is not None:
            if token.isdigit():
                digits.append(self._next())
            elif token == "." and (following := self._peek(1)) is not None and following.isdigit():
                digits.append(self._next())
            else:
                break
        return "".join(digits)

    def _letters(self, first: str) -> tuple[str, list[str]]:
        letters = [first]
        while (token := self._peek()) is not None and len(token) == 1 and token.isalpha():
            letters.append(self._next())

        *head, last = _split_spelled_functions(letters)
        kind, tail = self._word(last)
        return kind, [*head, *tail]

    def _word(self, word: str) -> tuple[str, list[str]]:
        if word in FUNCTIONS:
            return self._apply(FUNCTIONS[word])

        phrase, openers = LETTER_FUNCTIONS.get(word, (None, ""))
        if phrase and self._at_bracket(openers):
            return self._apply(phrase)
        return "term", [word]

    def _apply(self, phrase: str) -> tuple[str, list[str]]:
        words = [phrase]
        if self._peek() == "_":
            self._next()
            words = [phrase.removesuffix(" of"), "over", *self._argument(), "of"]
        return "apply", [*words, *self._bracketed()]

    def _at_bracket(self, openers: str = "([") -> bool:
        token = self._peek()
        if token == "\\left":
            token = self._peek(1)
        return token is not None and token in openers and token in BRACKETS

    def _bracketed(self) -> list[str]:
        if not self._at_bracket():
            return []

        self._skip("\\left")
        closer = BRACKETS[self._next()]
        words = self._sequence({closer, "\\right"})
        self._skip("\\right")
        self._skip(closer)
        return words

    def _command(self, name: str) -> tuple[str, list[str]]:
        if name == "|":
            return "apply", self._norm()
        if not name or not name[0].isalpha():
            word = ESCAPED.get(name, "")
            return "operator", [word] if word else []

        name = name.rstrip("*")

        if name in ("frac", "dfrac", "tfrac", "cfrac"):
            return "fraction", _fraction(self._argument(), self._argument())
        if name == "binom":
            return "term", [*self._argument(), "choose", *self._argument()]
        if name == "sqrt":
            index = self._optional_index()
            radicand = self._argument()
            return "term", [f"the {index} root of" if index else "the square root of", *radicand]
        if name in BIG_OPERATORS:
            return "operator", self._big_operator(BIG_OPERATORS[name])
        if name == "nabla":
            return "operator", self._gradient()
        if name in ACCENTS:
            return "term", [*self._argument(), ACCENTS[name]]
        if name in TEXT_FONTS:
            return self._text_font()
        if name in MATH_FONTS:
            content = self._argument()
            return self._word(content[0]) if len(content) == 1 else ("term", content)
        if name == "begin":
            return "term", self._environment()
        if name in ("end", "label", "tag"):
            self._raw_group()
            return "operator", []
        if name in SILENT:
            if name in ("left", "right"):
                self._skip(".")
            return "operator", []
        if name in FUNCTIONS:
            return self._apply(FUNCTIONS[name])
        if name in GREEK:
            return "term", [GREEK[name]]
        if name == "colon" and self._peek() == "=":
            self._next()
            return "operator", [IS_SET_TO]
        if name in SYMBOLS:
            return "operator", [SYMBOLS[name]]
        return "term", [name]

    def _norm(self) -> list[str]:
        inner = self._sequence({"\\|"})
        self._skip("\\|")
        return ["the norm of", *inner]

    def _optional_index(self) -> str:
        if self._peek() != "[":
            return ""

        self._next()
        parts: list[str] = []
        while self._peek() not in (None, "]"):
            parts.append(self._next())
        self._skip("]")
        return {"3": "cube"}.get("".join(parts), "".join(parts) + "th")

    def _big_operator(self, phrase: str) -> list[str]:
        lower: list[str] = []
        upper: list[str] = []

        while (token := self._peek()) in ("_", "^", "\\limits", "\\nolimits"):
            self._next()
            if token == "_":
                lower = self._argument()
            elif token == "^":
                upper = self._argument()

        if lower and upper:
            return [phrase, "from", *lower, "to", *upper, "of"]
        if lower:
            return [phrase, "over", *lower, "of"]
        return [phrase, "of"]

    def _gradient(self) -> list[str]:
        if self._peek() != "_":
            return ["the gradient of"]

        self._next()
        return ["the gradient with respect to", *self._argument(), "of"]

    def _text_font(self) -> tuple[str, list[str]]:
        """\\mathrm { V a r } reads as the word Var; anything richer is parsed normally."""
        if self._peek() == "{":
            end = self.position + 1
            while end < len(self.tokens) and self.tokens[end] != "}":
                end += 1
            letters = self.tokens[self.position + 1 : end]
            if letters and all(token.isalpha() for token in letters):
                self.position = end + 1
                return self._word("".join(letters))

        return "term", self._argument()

    def _environment(self) -> list[str]:
        name = self._raw_group().rstrip("*")
        if name in ("array", "tabular"):
            self._raw_group()  # column spec such as { r l r }

        body = self._sequence({"\\end"})
        if self._peek() == "\\end":
            self._next()
            self._raw_group()

        if all(word == "," for word in body):
            return []  # OCR sometimes emits empty grids of & and \\
        return ["the matrix", *body] if name in MATRIX_ENVIRONMENTS else body
