from pathlib import Path
from unittest import TestCase

from openpecha.pecha import Pecha
from openpecha.utils import read_json

from alignment_ann_transfer.commentary import CommentaryAlignmentTransfer

DATA_DIR = Path(__file__).parent / "data"


class TestCommentaryAlignmentTransfer(TestCase):
    def setUp(self):
        self.src_pecha = Pecha.from_path(DATA_DIR / "P2/I1DA9834A")
        self.tgt_pecha = Pecha.from_path(DATA_DIR / "P1/IB42962D2")
        self.commentary_pecha = Pecha.from_path(DATA_DIR / "P3/IDE145ACB")

    def test_get_alignment_mapping(self):
        commentary_transfer = CommentaryAlignmentTransfer()
        mapping = commentary_transfer.get_alignment_mapping(
            self.src_pecha, self.tgt_pecha
        )
        expected_mapping = read_json(DATA_DIR / "mapping.json")
        assert {str(k): v for k, v in mapping.items()} == expected_mapping

    def test_get_serialized_aligned_commentary(self):
        commentary_transfer = CommentaryAlignmentTransfer()
        aligned_segments = commentary_transfer.get_serialized_aligned_commentary(
            self.src_pecha, self.tgt_pecha, self.commentary_pecha
        )
        expected_aligned_segments = read_json(
            DATA_DIR / "aligned_commentary_segments.json"
        )
        assert aligned_segments == expected_aligned_segments

    def test_get_aligned_display_commentary(self):
        commentary_transfer = CommentaryAlignmentTransfer()
        aligned_commentary = commentary_transfer.get_aligned_display_commentary(
            self.src_pecha, self.tgt_pecha, self.commentary_pecha
        )
        expected_aligned_display_commentary = read_json(
            DATA_DIR / "aligned_display_commentary.json"
        )
        assert aligned_commentary == expected_aligned_display_commentary
