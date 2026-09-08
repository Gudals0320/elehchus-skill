"""Current skill files and local guide routes; no installer or network dependency."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDES = {f"stages/{name}.md" for name in (
    "topology", "research", "discovery", "web-evidence-loop", "lab"
)}


def markdown_links(document):
    # Generated-document examples in fenced blocks are not package dependencies.
    text = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*(?:\n|$)", "",
                  document.read_text(encoding="utf-8"))
    for match in re.finditer(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)", text):
        yield match.group(1) or match.group(2)


class CurrentPackageTests(unittest.TestCase):
    def test_current_runtime_files_exist(self):
        for name in {"LICENSE", "SKILL.md", "agents/openai.yaml"} | GUIDES:
            with self.subTest(file=name):
                self.assertTrue((REPO_ROOT / name).is_file(), name)

    def test_local_guide_links_resolve_and_all_stages_are_reachable(self):
        graph = {}
        documents = [REPO_ROOT / "SKILL.md", *(REPO_ROOT / "stages").glob("*.md")]
        for document in documents:
            name = document.relative_to(REPO_ROOT).as_posix()
            graph[name] = set()
            for link in markdown_links(document):
                with self.subTest(document=name, link=link):
                    parsed = urlsplit(link)
                    self.assertNotEqual(parsed.scheme, "file", "Guides must use portable paths")
                    self.assertFalse(re.match(r"^[A-Za-z]:", link), "Absolute drive path")
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    relative = Path(unquote(parsed.path))
                    self.assertFalse(relative.is_absolute(), link)
                    target = (document.parent / relative).resolve()
                    self.assertTrue(target.is_relative_to(REPO_ROOT), link)
                    self.assertTrue(target.is_file(), link)
                    graph[name].add(target.relative_to(REPO_ROOT).as_posix())
        self.assertTrue({"stages/topology.md", "stages/research.md"} <= graph["SKILL.md"])
        pending, reached = ["SKILL.md"], set()
        while pending:
            name = pending.pop()
            if name not in reached:
                reached.add(name)
                pending.extend(graph.get(name, set()))
        self.assertTrue(GUIDES <= reached, f"Unreachable guides: {GUIDES - reached}")


if __name__ == "__main__":
    unittest.main()
