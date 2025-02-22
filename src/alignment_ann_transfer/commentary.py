from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer import AlignmentTransfer
from alignment_ann_transfer.utils import extract_anns


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

        anns = extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, display_map in map.items():
            if display_map == []:
                continue
            commentary_text = anns[idx]["text"]
            display_idx = display_map[0][0]
            segments.append(f"<1><{display_idx}>{commentary_text}")
        return segments
