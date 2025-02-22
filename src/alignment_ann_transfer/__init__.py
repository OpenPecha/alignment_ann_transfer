from pathlib import Path
from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore


class AlignmentTransfer:
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

        map = self.map_layer_to_layer(transfer_layer, display_layer)

        # Clean up the layer
        new_tgt_layer.unlink()
        return map

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

    def map_layer_to_layer(
        self, src_layer: AnnotationStore, tgt_layer: AnnotationStore
    ):
        """
        1. Extract annotations from source and target layers
        2. Map the annotations from source to target layer
        src_layer -> tgt_layer (One to Many)
        """
        mapping: Dict = {}

        src_anns = self.extract_anns(src_layer)
        tgt_anns = self.extract_anns(tgt_layer)

        for src_idx, src_span in src_anns.items():
            src_start, src_end = src_span["Span"]["start"], src_span["Span"]["end"]
            mapping[src_idx] = []

            for tgt_idx, tgt_span in tgt_anns.items():
                tgt_start, tgt_end = tgt_span["Span"]["start"], tgt_span["Span"]["end"]

                # Check for mapping conditions
                if (
                    src_start
                    <= tgt_start
                    < src_end  # Target annotation starts within source
                    or src_start
                    < tgt_end
                    <= src_end  # Target annotation ends within source
                    or (
                        tgt_start < src_start and tgt_end > src_end
                    )  # Target fully contains source
                ) and not (
                    tgt_start == src_end or tgt_end == src_start
                ):  # No exact edge overlap
                    mapping[src_idx].append([tgt_idx, [tgt_start, tgt_end]])

        # Sort the mapping by source indices
        return dict(sorted(mapping.items()))
