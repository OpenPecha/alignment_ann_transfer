from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer import AlignmentTransfer


class TranslationAlignmentTransfer(AlignmentTransfer):
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

        map = self.map_layer_to_layer(transfer_layer, display_layer)

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

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, display_map in map.items():
            translation_text = anns[idx]["text"]
            display_idx = display_map[0][0]
            segments.append(f"<1><{display_idx}>{translation_text}")
        return segments

    def get_serialized_translation_display(
        self,
        root_pecha: Pecha,
        root_display_pecha: Pecha,
        translation_pecha: Pecha,
        translation_display_pecha: Pecha,
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>translation text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """
        root_map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)
        translation_map = self.get_translation_pechas_mapping(
            translation_pecha, translation_display_pecha
        )

        layer_path = next(translation_display_pecha.layer_path.rglob("*.json"))

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for src_idx, tgt_map in translation_map.items():
            translation_text = anns[src_idx]["text"]
            tgt_idx = tgt_map[0][0]

            root_idx = root_map[tgt_idx][0][0]
            segments.append(f"<1><{root_idx}>{translation_text}")
        return segments

    def get_aligned_translation(
        self, root_pecha: Pecha, root_display_pecha: Pecha, translation_pecha: Pecha
    ) -> List[Dict]:
        root_map = self.get_root_pechas_mapping(root_display_pecha, root_pecha)

        layer_path = next(translation_pecha.layer_path.rglob("*.json"))
        translation_anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        root_display_layer_path = next(root_display_pecha.layer_path.rglob("*.json"))
        root_display_anns = self.extract_anns(
            AnnotationStore(file=str(root_display_layer_path))
        )

        root_layer_path = next(root_pecha.layer_path.rglob("*.json"))
        root_anns = self.extract_anns(AnnotationStore(file=str(root_layer_path)))

        aligned_segments = []

        for root_display_idx, map in root_map.items():
            root_display_text = root_display_anns[root_display_idx]["text"]
            if not map:
                translation_texts = None

            elif not root_display_text.strip():
                translation_texts = None
            else:
                translation_texts = []
                for m in map:
                    root_idx = m[0]
                    if not root_anns[root_idx]["text"].strip():
                        continue

                    # Check if the root_idx is in the translation_anns
                    if root_idx not in translation_anns:
                        continue

                    translation_text = translation_anns[root_idx]["text"]
                    translation_texts.append(translation_text)

            aligned_segments.append(
                {
                    "root_display_text": root_display_text,
                    "translation_text": translation_texts,
                }
            )
        return aligned_segments
