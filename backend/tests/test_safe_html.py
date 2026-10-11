import unittest
import uuid

from app.core.utils.safe_html import sanitize_html
from app.schemas.reading.schema import ReadingCreate, ReadingUpdate


class SafeHtmlTests(unittest.TestCase):
    def test_keeps_simple_formatting(self):
        html = "<p>Hallo! Ich heiße <strong>Tom</strong>.<br>Ich komme aus <em>Berlin</em>.</p>"
        self.assertEqual(sanitize_html(html), html)

    def test_drops_scripts_handlers_and_links(self):
        dirty = (
            '<p onclick="x()">A</p><script>alert(1)</script><img src=x onerror=alert(1)>'
            '<a href="javascript:alert(1)">B</a><iframe src="//evil"></iframe><style>p{}</style>'
        )
        self.assertEqual(sanitize_html(dirty), "<p>A</p>B")

    def test_escapes_text_and_closes_tags(self):
        self.assertEqual(sanitize_html("<p>1 < 2 & <b>fett"), "<p>1 &lt; 2 &amp; <b>fett</b></p>")

    def test_reading_schemas_sanitize_content(self):
        created = ReadingCreate(lesson_id=uuid.uuid4(), title="T", content="<p>x</p><script>y</script>")
        self.assertEqual(created.content, "<p>x</p>")
        self.assertEqual(ReadingUpdate(content='<p style="c">z</p>').content, "<p>z</p>")
        self.assertIsNone(ReadingUpdate(title="only title").content)


if __name__ == "__main__":
    unittest.main()
