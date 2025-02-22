from pathlib import Path
from unittest import TestCase

from openpecha.pecha import Pecha
from openpecha.utils import read_json

from alignment_ann_transfer.translation import TranslationAlignmentTransfer

DATA_DIR = Path(__file__).parent / "data"


class TestTranslationAlignmentTransfer(TestCase):
    def setUp(self):
        self.root_pecha = Pecha.from_path(DATA_DIR / "P2/I73078576")
        self.root_display_pecha = Pecha.from_path(DATA_DIR / "P1/I15C4AA72")
        self.translation_pecha = Pecha.from_path(DATA_DIR / "P3/I4FA57826")
        self.translation_display_pecha = Pecha.from_path(DATA_DIR / "P4/I18FD6864")

    def test_get_root_pechas_mapping(self):
        translation_transfer = TranslationAlignmentTransfer()
        mapping = translation_transfer.get_root_pechas_mapping(
            self.root_pecha, self.root_display_pecha
        )
        expected_mapping = read_json(DATA_DIR / "root_pechas_mapping.json")
        assert {str(k): v for k, v in mapping.items()} == expected_mapping

    def test_get_translation_pechas_mapping(self):
        translation_transfer = TranslationAlignmentTransfer()
        mapping = translation_transfer.get_translation_pechas_mapping(
            self.translation_pecha, self.translation_display_pecha
        )
        expected_mapping = read_json(DATA_DIR / "translation_pechas_mapping.json")
        assert {str(k): v for k, v in mapping.items()} == expected_mapping

    def test_get_serialized_translation(self):
        translation_transfer = TranslationAlignmentTransfer()
        aligned_segments = translation_transfer.get_serialized_translation(
            self.root_pecha, self.root_display_pecha, self.translation_pecha
        )
        expected_aligned_segments = read_json(DATA_DIR / "serialized_translation.json")
        assert aligned_segments == expected_aligned_segments


work = TestTranslationAlignmentTransfer()
work.setUp()
work.test_get_root_pechas_mapping()
# work.test_get_translation_pechas_mapping()
work.test_get_serialized_translation()
