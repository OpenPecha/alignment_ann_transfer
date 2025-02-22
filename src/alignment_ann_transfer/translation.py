from pathlib import Path
from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer.utils import extract_anns, map_layer_to_layer


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

        map = map_layer_to_layer(transfer_layer, display_layer)

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

        map = map_layer_to_layer(transfer_layer, display_layer)

        # Clean up the layer
        new_tgt_layer_path.unlink()
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

        anns = extract_anns(AnnotationStore(file=str(layer_path)))

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
