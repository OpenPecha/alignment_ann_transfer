from typing import Dict, List, Tuple

from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer.utils import extract_anns, map_layer_to_layer


class CommentaryAlignmentTransfer:
    def get_root_pechas_mapping(
        self, root_pecha: Pecha, root_display_pecha: Pecha
    ) -> Dict[int, List]:
        """
        Get segmentation mapping from root_pecha -> root_pecha
        """
        self.base_update(root_pecha, root_display_pecha)
        display_layer, transfer_layer = self.get_display_transfer_layer(
            root_pecha, root_display_pecha
        )
        map = map_layer_to_layer(transfer_layer, display_layer)
        return map

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

    def get_root_display_and_commentary(
        self, root_pecha: Pecha, root_display_pecha: Pecha, commentary_pecha: Pecha
    ) -> List[Dict]:
        """
        Get map from display_layer -> transfer_layer
        """

        # From transfer -> display map get display -> transfer map
        map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)
        display_transfer_map = {}
        for t_idx, display_map in map.items():
            display_indicies = [d_map[0] for d_map in display_map]
            for d_idx in display_indicies:
                if d_idx not in display_transfer_map:
                    display_transfer_map[d_idx] = [t_idx]
                else:
                    display_transfer_map[d_idx].append(t_idx)

        # Get ann texts from display and commentary layer
        display_layer, _ = self.get_display_transfer_layer(
            root_pecha, root_display_pecha
        )
        display_anns = extract_anns(display_layer)

        layer_path = next(commentary_pecha.layer_path.rglob("*.json"))
        commentary_anns = extract_anns(AnnotationStore(file=str(layer_path)))

        aligned_commentary = []
        for d_idx, t_indicies in display_transfer_map.items():
            display_text = display_anns[d_idx]["text"]
            commentary_texts = []
            for t_idx in t_indicies:
                commentary_texts.append(commentary_anns[t_idx]["text"])

            aligned_commentary.append(
                {"display_text": display_text, "commentary_text": commentary_texts}
            )
        return aligned_commentary

    def base_update(self, root_pecha: Pecha, root_display_pecha: Pecha):
        """
        1. Take the layer from src pecha
        2. Migrate the layer to tgt pecha using base update
        """
        src_base_name = list(root_pecha.bases.keys())[0]
        tgt_base_name = list(root_display_pecha.bases.keys())[0]
        root_display_pecha.merge_pecha(root_pecha, src_base_name, tgt_base_name)

        src_layer_name = next(root_pecha.layer_path.rglob("*.json")).name
        new_layer = str(root_display_pecha.layer_path / tgt_base_name / src_layer_name)
        return AnnotationStore(file=new_layer)

    def get_display_transfer_layer(
        self, root_pecha: Pecha, root_display_pecha: Pecha
    ) -> Tuple[AnnotationStore, AnnotationStore]:
        src_layer_name = next(root_pecha.layer_path.rglob("*.json")).name
        display_layer_path = next(
            (
                layer_path
                for layer_path in root_display_pecha.layer_path.rglob("*.json")
                if layer_path.name != src_layer_name
            ),
            None,
        )
        new_layer_path = next(
            (
                layer_path
                for layer_path in root_display_pecha.layer_path.rglob("*.json")
                if layer_path.name == src_layer_name
            ),
            None,
        )

        display_layer = AnnotationStore(file=str(display_layer_path))
        new_layer = AnnotationStore(file=str(new_layer_path))
        return (display_layer, new_layer)
