from types import SimpleNamespace
import unittest

from read_my_paper.domain.narration import latex_to_speech, narration_from_document, normalize_text
from read_my_paper.infrastructure.paper_store import paper_id_from_name


class FakeDocument:
    def __init__(self, items):
        self.body = object()
        self.items = items

    def iterate_items(self, root):
        for item in self.items:
            yield item, 0


def item(label: str, text: str, page: int = 1):
    return SimpleNamespace(
        label=SimpleNamespace(value=label),
        text=text,
        prov=[SimpleNamespace(page_no=page)],
    )


class NarrationTests(unittest.TestCase):
    def test_excludes_tables_pictures_and_captions(self):
        document = FakeDocument(
            [
                item("title", "A paper"),
                item("paragraph", "The main result."),
                item("table", "never read"),
                item("picture", "never read"),
                item("caption", "never read"),
            ]
        )

        blocks, skipped = narration_from_document(document)

        self.assertEqual([block.text for block in blocks], ["A paper", "The main result."])
        self.assertEqual(skipped, {"table": 1, "picture": 1, "caption": 1})

    def test_starts_narration_at_the_abstract(self):
        document = FakeDocument(
            [
                item("title", "Paper title"),
                item("text", "Author One and Author Two"),
                item("section_header", "Abstract"),
                item("paragraph", "The paper starts here."),
            ]
        )

        blocks, skipped = narration_from_document(document)

        self.assertEqual([block.text for block in blocks], ["Abstract", "The paper starts here."])
        self.assertEqual(skipped, {"front_matter": 2})

    def test_normalizes_wrapped_hyphenated_text(self):
        self.assertEqual(normalize_text("inter-\n national  study"), "international study")

    def test_omits_acknowledgements_and_references(self):
        document = FakeDocument(
            [
                item("section_header", "Results"),
                item("paragraph", "The result is reproducible."),
                item("section_header", "Acknowledgements"),
                item("paragraph", "Thanks to everyone."),
                item("section_header", "Appendix"),
                item("paragraph", "Supplementary detail."),
                item("section_header", "References"),
                item("paragraph", "[1] A paper."),
                item("section_header", "Appendix B"),
                item("paragraph", "This remains excluded after references."),
            ]
        )

        blocks, skipped = narration_from_document(document)

        self.assertEqual(
            [block.text for block in blocks],
            ["Results", "The result is reproducible.", "Appendix", "Supplementary detail."],
        )
        self.assertEqual(skipped, {"acknowledgements": 2, "references": 4})

    def test_removes_numeric_bracket_citations(self):
        self.assertEqual(
            normalize_text("A result [1] agrees with prior work [2, 3; 5-7]."),
            "A result agrees with prior work.",
        )

    def test_derives_a_readable_paper_id_from_its_filename(self):
        self.assertEqual(
            paper_id_from_name("Delving Deep into Rectifiers (final).pdf"),
            "delving-deep-into-rectifiers-final",
        )

    def test_reads_common_latex_in_english(self):
        self.assertEqual(
            latex_to_speech(r"\frac{\partial E}{\partial a} = \sum_{i=1}^{n} x_i"),
            "the partial derivative of E with respect to a equals the sum from i equals 1 to n of x subscript i",
        )

    def test_reads_docling_spaced_latex(self):
        self.assertEqual(
            latex_to_speech(
                r"\begin{array} { r l } { V a r [ y _ { l } ] } & { = \frac { 1 } { 2 } n _ { l } V a r [ w _ { l } ] } \end{array}"
            ),
            "the variance of y subscript l equals one half n subscript l times the variance of w subscript l",
        )

    def test_speaks_unicode_math_ocr(self):
        document = FakeDocument([item("text", "∂E ∂a = ∑i ∑yi ∂E ∂f (yi)")])

        blocks, skipped = narration_from_document(document)

        self.assertEqual(
            [block.text for block in blocks],
            ["the partial derivative of E with respect to a equals sum i sum yi "
             "the partial derivative of E with respect to f (yi)"],
        )
        self.assertEqual(skipped, {})


if __name__ == "__main__":
    unittest.main()
