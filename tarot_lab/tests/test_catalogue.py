from collections import Counter
import unittest
from pydantic import ValidationError
from lumi_core.catalog.tarot import CARDS, BY_ID, meanings
from lumi_core.catalog.zodiac import SIGN_ELEMENTS
from tarot_lab.fixtures.meanings_v1 import fixture_chunks, tarot_chunks, validate_chunks
from tarot_lab.schemas import ReadingInput

class CatalogueTests(unittest.TestCase):
    def test_complete_catalogue(self):
        self.assertEqual(len(BY_ID),78)
        self.assertEqual(len(meanings()),156)
        self.assertEqual(Counter(c.suit for c in CARDS),{'':22,'wands':14,'cups':14,'swords':14,'pentacles':14})
        self.assertTrue(all(c.element is None for c in CARDS if c.arcana=='major'))
        self.assertEqual(len(SIGN_ELEMENTS),12)

    def test_authored_corpus_coverage_and_direction_distinction(self):
        self.assertEqual(len(fixture_chunks()),30)
        rows=tarot_chunks()
        validate_chunks(rows)
        self.assertEqual(len(rows),180)
        self.assertEqual(len([r for r in rows if r['topic']=='general']),156)
        for row in rows:
            self.assertIn(row['card_id'],BY_ID)
            self.assertEqual(row['source_kind'],'authored')

    def test_public_input_rejects_draws_and_unknown_profiles(self):
        valid={'mbti':'INTJ','zodiac_id':'aquarius','question':'어떻게 시작할까?'}
        self.assertEqual(ReadingInput(**valid).mbti,'INTJ')
        for extra in [{'draws':[]},{'card_id':'major-16-tower'},{'mbti':'NOPE'},{'zodiac_id':'unknown'},{'question':' '}]:
            with self.assertRaises(ValidationError): ReadingInput(**(valid|extra))
