"""Published-byte integrity checks; no model calls and no frozen fixture mutation."""
from pathlib import Path
import tempfile
import unittest

import publication_integrity
import runner


class PublicationIntegrityTests(unittest.TestCase):
    def test_utf8_writer_has_explicit_bytes_including_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "visible.md"
            text = "한글 응답\n다음 줄\n"
            runner.write_utf8(path, text)
            self.assertEqual(path.read_bytes(), text.encode("utf-8"))
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_crlf_metadata_correction_preserves_text_digests_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            turn = root / "turn-01"
            turn.mkdir()
            files = {"input.md": b"INPUT\r\n", "answer.md": b"ANSWER\r\n", "events.jsonl": b'{"type":"sample"}\r\n'}
            for name, data in files.items():
                (turn / name).write_bytes(data)
            summary = {"turns": [{"number": 1, "input_sha256": "pretransport-text-digest",
                                  "answer_sha256": "prepublication-text-digest",
                                  "published_input_sha256": runner.sha(b"INPUT\n"),
                                  "published_answer_sha256": runner.sha(b"ANSWER\n")}], "artifacts": {}}
            updates = publication_integrity.update_fields(summary, root)
            actual = summary["turns"][0]
            self.assertEqual(actual["input_sha256"], "pretransport-text-digest")
            self.assertEqual(actual["answer_sha256"], "prepublication-text-digest")
            self.assertEqual(actual["published_input_sha256"], runner.sha(files["input.md"]))
            self.assertEqual(actual["published_answer_sha256"], runner.sha(files["answer.md"]))
            self.assertEqual(actual["published_events_sha256"], runner.sha(files["events.jsonl"]))
            self.assertEqual(sum(item["kind"] == "corrected" for item in updates), 2)
            self.assertEqual({name: (turn / name).read_bytes() for name in files}, files)


if __name__ == "__main__":
    unittest.main()
