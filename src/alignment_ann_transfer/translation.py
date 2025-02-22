from pathlib import Path
from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore


class TranslationAlignmentTransfer:
    def get_first_layer_path(self, pecha: Pecha) -> Path:
        return next(pecha.layer_path.rglob("*.json"))

    def get_root_pechas_mapping(
        self, root_pecha: Pecha, root_display_pecha: Pecha
    ) -> Dict[int, List]:
        """
        Get segmentation mapping from root_pecha -> root_display_pecha
        """
        display_layer_path = self.get_first_layer_path(root_display_pecha)
        new_tgt_layer = self.base_update(root_pecha, root_display_pecha)

        display_layer = AnnotationStore(file=str(display_layer_path))
        transfer_layer = AnnotationStore(file=str(new_tgt_layer))

        map = self.map_display_to_transfer_layer(display_layer, transfer_layer)

        # Clean up the layer
        new_tgt_layer.unlink()
        return map

    def get_translation_pechas_mapping(
        self, translation_pecha: Pecha, translation_display_pecha: Pecha
    ) -> Dict[int, List]:
        """
        Get Segmentation mapping from translation display pecha -> translation pecha
        """
        display_layer_path = self.get_first_layer_path(translation_pecha)
        new_tgt_layer_path = self.base_update(
            translation_display_pecha, translation_pecha
        )

        display_layer = AnnotationStore(file=str(display_layer_path))
        transfer_layer = AnnotationStore(file=str(new_tgt_layer_path))

        map = self.map_display_to_transfer_layer(display_layer, transfer_layer)
        return map

    def get_serialized_translation(
        self, root_pecha: Pecha, root_display_pecha: Pecha, translation_pecha: Pecha
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>translation text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """
        map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)
        layer_path = next(translation_pecha.layer_path.rglob("*.json"))

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, display_map in map.items():
            translation_text = anns[idx]["text"]
            display_idx = display_map[0][0]
            segments.append(f"<1><{display_idx}>{translation_text}")
        return segments

    def base_update(self, src_pecha: Pecha, tgt_pecha: Pecha) -> Path:
        """
        1. Take the layer from src pecha
        2. Migrate the layer to tgt pecha using base update
        """
        src_base_name = list(src_pecha.bases.keys())[0]
        tgt_base_name = list(tgt_pecha.bases.keys())[0]
        tgt_pecha.merge_pecha(src_pecha, src_base_name, tgt_base_name)

        src_layer_name = next(src_pecha.layer_path.rglob("*.json")).name
        new_layer_path = tgt_pecha.layer_path / tgt_base_name / src_layer_name
        return new_layer_path

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
