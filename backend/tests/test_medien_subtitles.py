"""Subtitle files of Medienwelt films (`app/services/medien/subtitles.py`): formats, encodings, sanitising, checks, output.
Pure unit tests — no database, no files."""

import unittest

from app.services.medien import subtitles as s

SRT = "1\n00:00:00,500 --> 00:00:03,000\nGuten Tag Welt\n\n2\n00:00:03,500 --> 00:00:05,500\nAuf Wiedersehen\nund bis bald\n"
VTT = "WEBVTT\n\n00:00:00.500 --> 00:00:03.000\nSalom dunyo\n\nintro\n00:00:03.500 --> 00:00:05.500 align:start\nXayr\n"


def codes(analysis):
    return {w["code"] for w in analysis.warnings}


class TestFormats(unittest.TestCase):
    def test_srt_with_commas_and_numbers(self):
        a = s.analyze(SRT.encode())
        self.assertEqual(a.format, "srt")
        self.assertEqual([(c.start, c.end, c.text) for c in a.cues], [(500, 3000, "Guten Tag Welt"), (3500, 5500, "Auf Wiedersehen\nund bis bald")])
        self.assertEqual(a.warnings, [])

    def test_vtt_with_identifier_and_cue_settings(self):
        a = s.analyze(VTT.encode())
        self.assertEqual(a.format, "vtt")
        self.assertEqual([(c.start, c.end, c.text) for c in a.cues], [(500, 3000, "Salom dunyo"), (3500, 5500, "Xayr")])

    def test_vtt_single_line_text_without_identifiers_is_kept(self):
        a = s.analyze(b"WEBVTT\n\n00:01.000 --> 00:02.000\n1984\n\n00:03.000 --> 00:04.000\nHallo\n")
        self.assertEqual([c.text for c in a.cues], ["1984", "Hallo"])

    def test_vtt_short_timestamps_and_notes(self):
        a = s.analyze(b"WEBVTT - title\n\nNOTE a comment\nover two lines\n\n01:02.250 --> 01:04.000\nHi\n")
        self.assertEqual((a.cues[0].start, a.cues[0].end), (62250, 64000))

    def test_srt_without_blank_lines_between_cues(self):
        a = s.analyze(b"1\n00:00:01,000 --> 00:00:02,000\nEins\n2\n00:00:03,000 --> 00:00:04,000\nZwei\n")
        self.assertEqual([c.text for c in a.cues], ["Eins", "Zwei"])

    def test_crlf_bom_and_milliseconds_of_one_or_two_digits(self):
        raw = "﻿1\r\n00:00:01,5 --> 00:00:02,25\r\nTest\r\n".encode("utf-8")
        a = s.analyze(raw)
        self.assertEqual((a.cues[0].start, a.cues[0].end), (1500, 2250))

    def test_not_a_subtitle_is_refused(self):
        for raw, code in ((b"", "SUBTITLE_EMPTY"), (b"   \n", "SUBTITLE_EMPTY"), (b"just some text\nwithout times", "SUBTITLE_FORMAT"),
                          (b"\x00\x01\x02binary", "SUBTITLE_BINARY"), (b"1\n00:00:05,000 --> 00:00:01,000\nbackwards\n", "SUBTITLE_NO_CUES"),
                          (b"1\n00:00:01,000 --> 00:00:02,000\n\n", "SUBTITLE_NO_CUES")):
            with self.assertRaises(s.SubtitleError, msg=raw) as ctx:
                s.analyze(raw)
            self.assertEqual(ctx.exception.code, code, raw)

    def test_too_many_cues(self):
        blocks = "".join(f"{i}\n00:00:00,000 --> 00:00:01,000\nx\n\n" for i in range(s.MAX_CUES + 1))
        with self.assertRaises(s.SubtitleError) as ctx:
            s.analyze(blocks.encode())
        self.assertEqual(ctx.exception.code, "SUBTITLE_TOO_LARGE")


class TestEncodings(unittest.TestCase):
    def test_windows_1252_german(self):
        a = s.analyze("1\n00:00:01,000 --> 00:00:02,000\nGrüße aus Köln, Straße\n".encode("cp1252"))
        self.assertEqual(a.cues[0].text, "Grüße aus Köln, Straße")
        self.assertEqual(a.encoding, "windows-1252")
        self.assertIn("ENCODING_CONVERTED", codes(a))

    def test_utf16_with_bom(self):
        a = s.analyze("1\n00:00:01,000 --> 00:00:02,000\nÄpfel\n".encode("utf-16"))
        self.assertEqual((a.cues[0].text, a.encoding), ("Äpfel", "utf-16"))

    def test_uzbek_apostrophes_survive(self):
        a = s.analyze("1\n00:00:01,000 --> 00:00:02,000\nO‘zbekcha, o'qish, g‘alaba\n".encode("utf-8"))
        self.assertEqual(a.cues[0].text, "O‘zbekcha, o'qish, g‘alaba")


class TestSanitising(unittest.TestCase):
    def test_markup_is_removed_and_entities_decoded(self):
        raw = ("1\n00:00:01,000 --> 00:00:02,000\n<i>Hallo</i> <font color=\"red\">Welt</font><script>alert(1)</script>\n"
               "<v Max>Tom &amp; Jerry &lt;3</v><b>fett</b><00:00:01.500>x<c.red>y</c>\n").encode()
        text = s.analyze(raw).cues[0].text
        self.assertEqual(text, "Hallo Weltalert(1)\nTom & Jerry <3fettxy")
        self.assertNotIn("<script", text)

    def test_br_becomes_a_line_break_and_control_characters_go(self):
        a = s.analyze("1\n00:00:01,000 --> 00:00:02,000\nEins<br/>Zwei​\x07 drei\n".encode())
        self.assertEqual(a.cues[0].text, "Eins\nZwei drei")

    def test_output_escapes_markup_characters(self):
        a = s.analyze(b"1\n00:00:01,000 --> 00:00:02,000\n&lt;img src=x onerror=alert(1)&gt; &amp; a --&gt; b\n")
        vtt = s.to_vtt(a.cues).decode()
        self.assertNotIn("<img", vtt)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt; &amp; a --&gt; b", vtt)
        # reading it back gives the same plain text
        self.assertEqual(s.read_cues(vtt.encode())[0].text, "<img src=x onerror=alert(1)> & a --> b")

    def test_long_text_is_cut(self):
        a = s.analyze(("1\n00:00:01,000 --> 00:00:02,000\n" + "x" * 900 + "\n").encode())
        self.assertEqual(len(a.cues[0].text), s.MAX_CUE_TEXT)
        self.assertIn("TEXT_CUT", codes(a))


class TestRepairAndChecks(unittest.TestCase):
    def test_broken_blocks_are_skipped_not_fatal(self):
        raw = ("1\n00:00:01,000 --> 00:00:02,000\nGut\n\n2\n00:00:xx,000 --> 00:00:04,000\nKaputt\n\n"
               "3\n00:00:05,000 --> 00:00:04,000\nRückwärts\n\n4\n00:00:06,000 --> 00:00:07,000\n\n\n5\n00:00:08,000 --> 00:00:09,000\nAuch gut\n").encode()
        a = s.analyze(raw)
        self.assertEqual([c.text for c in a.cues], ["Gut", "Auch gut"])
        self.assertTrue({"BAD_TIMESTAMP", "BAD_RANGE", "EMPTY_CUE"} <= codes(a))

    def test_unsorted_cues_are_sorted(self):
        a = s.analyze(b"1\n00:00:05,000 --> 00:00:06,000\nB\n\n2\n00:00:01,000 --> 00:00:02,000\nA\n")
        self.assertEqual([c.text for c in a.cues], ["A", "B"])
        self.assertIn("UNSORTED", codes(a))

    def test_overlap_short_long_and_long_lines_are_reported(self):
        raw = ("1\n00:00:01,000 --> 00:00:04,000\n" + "w" * 100 + "\n\n2\n00:00:03,000 --> 00:00:03,100\nkurz\n\n3\n00:00:10,000 --> 00:00:30,000\nlang\n").encode()
        self.assertTrue({"OVERLAP", "VERY_SHORT", "VERY_LONG", "LONG_LINE"} <= codes(s.analyze(raw)))

    def test_fit_to_the_video_length(self):
        two_hours = 2 * 3600 * 1000
        late = b"1\n01:50:00,000 --> 01:50:05,000\nSpaet\n"
        self.assertNotIn("BEYOND_VIDEO", codes(s.analyze(late, two_hours)))
        self.assertIn("BEYOND_VIDEO", codes(s.analyze(late, 20 * 60 * 1000)))   # a 20 min clip with a 1:50 h subtitle
        self.assertIn("ENDS_EARLY", codes(s.analyze(b"1\n00:00:01,000 --> 00:00:05,000\nNur Anfang\n", two_hours)))
        self.assertNotIn("BEYOND_VIDEO", codes(s.analyze(late)))                # length unknown: no judgement
        # rounded minutes of an older film: one minute of tolerance
        self.assertNotIn("BEYOND_VIDEO", codes(s.analyze(b"1\n00:01:20,000 --> 00:01:30,000\nEnde\n", 60_000)))


class TestOutput(unittest.TestCase):
    def test_roundtrip_through_the_normalised_file(self):
        a = s.analyze(SRT.encode())
        vtt = s.to_vtt(a.cues)
        self.assertTrue(vtt.startswith(b"WEBVTT\n\n00:00:00.500 --> 00:00:03.000\nGuten Tag Welt\n\n"))
        self.assertEqual([(c.start, c.end, c.text) for c in s.read_cues(vtt)], [(c.start, c.end, c.text) for c in a.cues])

    def test_old_unsanitised_files_are_sanitised_on_read(self):
        old = b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<script>x()</script>Hallo <b>Welt</b>\n"
        self.assertEqual(s.read_cues(old)[0].text, "x()Hallo Welt")

    def test_cues_json_and_report(self):
        a = s.analyze(VTT.encode())
        self.assertEqual(s.cues_json(a.cues), [[500, 3000, "Salom dunyo"], [3500, 5500, "Xayr"]])
        rep = a.report()
        self.assertEqual((rep["cue_count"], rep["first_ms"], rep["last_ms"], rep["format"]), (2, 500, 5500, "vtt"))

    def test_hours_in_timestamps(self):
        self.assertTrue(s.to_vtt([s.Cue(3_723_004, 3_725_000, "x")]).startswith(b"WEBVTT\n\n01:02:03.004 --> 01:02:05.000\n"))


if __name__ == "__main__":
    unittest.main()
