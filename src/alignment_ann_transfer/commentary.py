from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer import AlignmentTransfer
from alignment_ann_transfer.utils import parse_root_mapping


class CommentaryAlignmentTransfer(AlignmentTransfer):
    def get_serialized_commentary(
        self, root_pecha: Pecha, root_display_pecha: Pecha, commentary_pecha: Pecha
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>commentary text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """
        map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)
        layer_path = next(commentary_pecha.layer_path.rglob("*.json"))

        anns = self.extract_commentary_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for ann in anns:
            root_indices = parse_root_mapping(ann["root_idx_mapping"])
            first_idx = root_indices[0]
            commentary_text = ann["text"]
            display_idx = map[first_idx][0][0]
            segments.append(f"<1><{display_idx}>{commentary_text}")
        return segments

    def extract_commentary_anns(self, layer: AnnotationStore) -> List[Dict]:
        """
        Extract annotation from layer(STAM)
        """
        anns = []
        for ann in layer.annotations():
            start, end = ann.offset().begin().value(), ann.offset().end().value()
            ann_metadata = {}
            for data in ann:
                ann_metadata[data.key().id()] = str(data.value())
            anns.append(
                {
                    "Span": {"start": start, "end": end},
                    "text": str(ann),
                    "root_idx_mapping": ann_metadata["root_idx_mapping"],
                }
            )
        return anns
