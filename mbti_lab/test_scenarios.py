import unittest
from collections import Counter
from mbti_lab.scenarios import cards, SUGGESTIONS
from mbti_lab.data import TRAITS


class ScenarioTests(unittest.TestCase):
    def test_each_suggestion_has_explicit_evidence(self):
        rows = cards()
        self.assertEqual(len(rows), 600)
        self.assertEqual(len({r['id'] for r in rows}), 600)
        self.assertEqual(len({r['text'] for r in rows}), 600)
        self.assertEqual(len(SUGGESTIONS), 24)
        by_id = {key: trait for key, trait, _ in SUGGESTIONS}
        for row in rows:
            self.assertTrue(set(row['traits']) <= set(TRAITS))
            self.assertEqual(set(row['traits']), {by_id[key] for key in row['tips']})
        self.assertEqual({key for row in rows for key in row['tips']}, set(by_id))

    def test_profiles_have_ten_distinct_facets_and_traceable_sources(self):
        rows = cards()
        profiles = [r for r in rows if r['kind'] == 'interpretation']
        self.assertEqual(Counter(r['subject_kind'] for r in profiles), {'mbti': 160, 'zodiac': 120})
        counts = Counter((r['subject_kind'], r['subject']) for r in profiles)
        self.assertEqual(len(counts), 28)
        self.assertEqual(set(counts.values()), {10})
        self.assertEqual(len({r['document_id'] for r in rows}), 64)
        for row in profiles:
            self.assertTrue(row['source_url'].startswith('https://'))
            self.assertTrue(row['editorial_note'])
        for subject in counts:
            self.assertEqual(len({r['facet'] for r in profiles if (r['subject_kind'], r['subject']) == subject}), 10)

    def test_existing_cards_keep_their_stable_ids_and_text(self):
        from mbti_lab.scenarios import RAW_CARDS
        for index, (row, (_, original, _)) in enumerate(zip(cards(), RAW_CARDS), 1):
            self.assertEqual(row['id'], f'scenario-{index:02}')
            self.assertEqual(row['text'], original)
