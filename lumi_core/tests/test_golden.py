import hashlib
import json
import unittest
from pathlib import Path
from lumi_core.corpus.lumi import cards
from lumi_core.corpus.mbti import result

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((Path(__file__).parent/'golden/beta.json').read_text())
def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

class GoldenTests(unittest.TestCase):
    def test_static_corpus_and_responses_unchanged(self):
        self.assertEqual(digest(cards()), GOLDEN['cards'])
        for code, expected in GOLDEN['results'].items():
            self.assertEqual(digest(result(code)), expected, code)

    def test_protected_files_unchanged(self):
        for name, expected in GOLDEN['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
