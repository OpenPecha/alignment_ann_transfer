from typing import Dict, List, Tuple

from openpecha.pecha import Pecha
from stam import AnnotationStore


class TranslationAlignmentTransfer:
    def get_alignment_mapping(
        self, src_pecha: Pecha, tgt_pecha: Pecha
    ) -> Dict[int, List]:
        self.base_update(src_pecha, tgt_pecha)
        display_layer, transfer_layer = self.get_display_transfer_layer(
            src_pecha, tgt_pecha
        )
        mapping = self.map_display_to_transfer_layer(display_layer, transfer_layer)
        return mapping

    def get_ann_text_by_idx(self, anns: Dict, idx: int):
        for root_idx, ann_metadata in anns.items():
            if str(root_idx) == str(idx):
                return ann_metadata["text"]
        return None

    def get_aligned_translation_segments(
        self, src_pecha: Pecha, tgt_pecha: Pecha, translation_pecha: Pecha
    ):
        """
        Input: mapping from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>translation text
        Note: From many relation in display layer, take first idx (Sefaria mapping limitation)
        """
        mapping = self.get_alignment_mapping(src_pecha, tgt_pecha)
        layer_path = next(translation_pecha.layer_path.rglob("*.json"))

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, display_mapping in mapping.items():
            translation_text = self.get_ann_text_by_idx(anns, idx)
            display_idx = display_mapping[0][0]
            segments.append(f"<1><{display_idx}>{translation_text}")
        return segments

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
        mapping: Dict = {}

        display_anns = self.extract_anns(display_layer)
        transfer_anns = self.extract_anns(transfer_layer)

        for t_idx, t_span in transfer_anns.items():
            t_start, t_end = (
                t_span["Span"]["start"],
                t_span["Span"]["end"],
            )
            mapping[t_idx] = []
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
                    mapping[t_idx].append([d_idx, [d_start, d_end]])
        # Sort the mapping
        mapping = dict(sorted(mapping.items()))
        return mapping
