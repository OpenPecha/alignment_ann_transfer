from pathlib import Path
from unittest import TestCase

from openpecha.pecha import Pecha
from openpecha.utils import read_json

from alignment_ann_transfer.translation import TranslationAlignmentTransfer

DATA_DIR = Path(__file__).parent / "data"


class TestTranslationAlignmentTransfer(TestCase):
    def setUp(self):
        self.src_pecha = Pecha.from_path(DATA_DIR / "P2/I73078576")
        self.tgt_pecha = Pecha.from_path(DATA_DIR / "P1/I15C4AA72")
        self.translation_pecha = Pecha.from_path(DATA_DIR / "P3/I4FA57826")

    def test_translation_ann_transfer(self):
        translation_transfer = TranslationAlignmentTransfer()
        mapping = translation_transfer.get_alignment_mapping(
            self.src_pecha, self.tgt_pecha
        )
        expected_mapping = read_json(DATA_DIR / "expected_mapping.json")
        assert {str(k): v for k, v in mapping.items()} == expected_mapping
