from pathlib import Path
from unittest import TestCase

from openpecha.pecha import Pecha
from openpecha.utils import read_json

from alignment_ann_transfer.commentary import CommentaryAlignmentTransfer

DATA_DIR = Path(__file__).parent / "data"


class TestCommentaryAlignmentTransfer(TestCase):
    def setUp(self):
        self.root_pecha = Pecha.from_path(DATA_DIR / "P2/IC7760088")
        self.root_display_pecha = Pecha.from_path(DATA_DIR / "P1/IA6E66F92")
        self.commentary_pecha = Pecha.from_path(DATA_DIR / "P3/I77BD6EA9")

    def test_get_root_pechas_mapping(self):
        commentary_transfer = CommentaryAlignmentTransfer()
        mapping = commentary_transfer.get_root_pechas_mapping(
            self.root_pecha, self.root_display_pecha
        )
        expected_mapping = read_json(DATA_DIR / "root_pechas_mapping.json")
        assert {str(k): v for k, v in mapping.items()} == expected_mapping

    def test_get_serialized_commentary(self):
        commentary_transfer = CommentaryAlignmentTransfer()
        serialized_json = commentary_transfer.get_serialized_commentary(
            self.root_pecha, self.root_display_pecha, self.commentary_pecha
        )
        expected_serialized_json = read_json(DATA_DIR / "serialized_commentary.json")
        assert serialized_json == expected_serialized_json
