from typing import Dict, List, Tuple

from openpecha.pecha import Pecha
from stam import AnnotationStore


class CommentaryAlignmentTransfer:
    def get_alignment_mapping(
        self, src_pecha: Pecha, tgt_pecha: Pecha
    ) -> Dict[int, List]:
        self.base_update(src_pecha, tgt_pecha)
        display_layer, transfer_layer = self.get_display_transfer_layer(
            src_pecha, tgt_pecha
        )
        map = self.map_display_to_transfer_layer(display_layer, transfer_layer)
        return map

    def get_serialized_aligned_commentary(
        self, src_pecha: Pecha, tgt_pecha: Pecha, commentary_pecha: Pecha
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>commentary text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """
        map = self.get_alignment_mapping(src_pecha, tgt_pecha)
        layer_path = next(commentary_pecha.layer_path.rglob("*.json"))

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, display_map in map.items():
            commentary_text = anns[idx]["text"]
            display_idx = display_map[0][0]
            segments.append(f"<1><{display_idx}>{commentary_text}")
        return segments

    def get_aligned_display_commentary(
        self, src_pecha: Pecha, tgt_pecha: Pecha, commentary_pecha: Pecha
    ) -> List[Dict]:
        """
        Get map from display_layer -> transfer_layer
        """

        # From transfer -> display map get display -> transfer map
        map = self.get_alignment_mapping(src_pecha, tgt_pecha)
        display_transfer_map = {}
        for t_idx, display_map in map.items():
            display_indicies = [d_map[0] for d_map in display_map]
            for d_idx in display_indicies:
                if d_idx not in display_transfer_map:
                    display_transfer_map[d_idx] = [t_idx]
                else:
                    display_transfer_map[d_idx].append(t_idx)

        # Get ann texts from display and commentary layer
        display_layer, _ = self.get_display_transfer_layer(src_pecha, tgt_pecha)
        display_anns = self.extract_anns(display_layer)

        layer_path = next(commentary_pecha.layer_path.rglob("*.json"))
        commentary_anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

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

    def base_update(self, src_pecha: Pecha, tgt_pecha: Pecha):
        """
        1. Take the layer from src pecha
        2. Migrate the layer to tgt pecha using base update
        """
        src_base_name = list(src_pecha.bases.keys())[0]
        tgt_base_name = list(tgt_pecha.bases.keys())[0]
        tgt_pecha.merge_pecha(src_pecha, src_base_name, tgt_base_name)

        src_layer_name = next(src_pecha.layer_path.rglob("*.json")).name
        new_layer = str(tgt_pecha.layer_path / tgt_base_name / src_layer_name)
        return AnnotationStore(file=new_layer)

    def get_display_transfer_layer(
        self, src_pecha: Pecha, tgt_pecha: Pecha
    ) -> Tuple[AnnotationStore, AnnotationStore]:
        src_layer_name = next(src_pecha.layer_path.rglob("*.json")).name
        display_layer_path = next(
            (
                layer_path
                for layer_path in tgt_pecha.layer_path.rglob("*.json")
                if layer_path.name != src_layer_name
            ),
            None,
        )
        new_layer_path = next(
            (
                layer_path
                for layer_path in tgt_pecha.layer_path.rglob("*.json")
                if layer_path.name == src_layer_name
            ),
            None,
        )

        display_layer = AnnotationStore(file=str(display_layer_path))
        new_layer = AnnotationStore(file=str(new_layer_path))
        return (display_layer, new_layer)

    def extract_anns(self, layer: AnnotationStore) -> Dict:
        """
        Extract annotation from layer(STAM)
        """
        anns = {}
        for ann in layer.annotations():
            start, end = ann.offset().begin().value(), ann.offset().end().value()
            ann_metadata = {}
            for data in ann:
                ann_metadata[data.key().id()] = str(data.value())
            anns[int(ann_metadata["root_idx_mapping"])] = {
                "Span": {"start": start, "end": end},
                "text": str(ann),
                "root_idx_mapping": int(ann_metadata["root_idx_mapping"]),
            }
        return anns

    def map_display_to_transfer_layer(
        self, display_layer: AnnotationStore, transfer_layer: AnnotationStore
    ):
        """
        1. Extract annotations from display and transfer layer
        2. Map the annotations from display to transfer layer
        transfer_layer -> display_layer (One to Many)
        """
        map: Dict = {}

        display_anns = self.extract_anns(display_layer)
        transfer_anns = self.extract_anns(transfer_layer)

        for t_idx, t_span in transfer_anns.items():
            t_start, t_end = (
                t_span["Span"]["start"],
                t_span["Span"]["end"],
            )
            map[t_idx] = []
            for d_idx, d_span in display_anns.items():
                d_start, d_end = (
                    d_span["Span"]["start"],
                    d_span["Span"]["end"],
                )
                flag = False

                # In between
                if t_start <= d_start <= t_end - 1 or t_start <= d_end - 1 <= t_end - 1:
                    flag = True

                # Contain
                if d_start < t_start and d_end > t_end:
                    flag = True

                # Overlap
                if d_start == t_end or d_end == t_start:
                    flag = False

                if flag:
                    map[t_idx].append([d_idx, [d_start, d_end]])
        # Sort the map
        map = dict(sorted(map.items()))
        return map
