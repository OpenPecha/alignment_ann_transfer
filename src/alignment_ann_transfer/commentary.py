from typing import Dict, List

from openpecha.pecha import Pecha
from stam import AnnotationStore

from alignment_ann_transfer import AlignmentTransfer
from alignment_ann_transfer.utils import parse_root_mapping


class CommentaryAlignmentTransfer(AlignmentTransfer):
    def get_commentary_pechas_mapping(
        self, commentary_pecha: Pecha, commentary_display_pecha: Pecha
    ) -> Dict[int, List]:
        """
        Get Segmentation mapping from commentary display pecha -> commentary pecha(root idx mapping)
        """
        display_layer_path = self.get_first_layer_path(commentary_pecha)
        new_tgt_layer_path = self.base_update(
            commentary_display_pecha, commentary_pecha
        )

        display_layer = AnnotationStore(file=str(display_layer_path))
        transfer_layer = AnnotationStore(file=str(new_tgt_layer_path))

        map = self.map_commentary_layer_to_layer(transfer_layer, display_layer)

        # Clean up the layer
        new_tgt_layer_path.unlink()
        return map

    def get_serialized_commentary(
        self, root_pecha: Pecha, root_display_pecha: Pecha, commentary_pecha: Pecha
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>commentary text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """

        def is_empty(text):
            """Check if text is empty or contains only newlines."""
            return not text.strip().replace("\n", "")

        map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)

        root_display_layer_path = next(root_display_pecha.layer_path.rglob("*.json"))
        root_display_anns = self.extract_anns(
            AnnotationStore(file=str(root_display_layer_path))
        )

        root_layer_path = next(root_pecha.layer_path.rglob("*.json"))
        root_anns = self.extract_anns(AnnotationStore(file=str(root_layer_path)))

        commentary_layer_path = next(commentary_pecha.layer_path.rglob("*.json"))
        commentary_anns = self.extract_commentary_anns(
            AnnotationStore(file=str(commentary_layer_path))
        )

        segments = []
        for ann in commentary_anns:
            root_indices = parse_root_mapping(ann["root_idx_mapping"])
            first_idx = root_indices[0]
            commentary_text = ann["text"]

            # # If the commentary text is empty, skip
            if is_empty(commentary_text):
                curr_segment = commentary_text

            # If aligned root does not have text, dont add any mapping
            elif not map.get(first_idx):
                curr_segment = commentary_text

            # If the root text is empty, dont add any mapping
            elif is_empty(root_anns[first_idx]["text"]):
                curr_segment = commentary_text
            else:
                display_idx = map[first_idx][0][0]
                if display_idx in root_display_anns and not is_empty(
                    root_display_anns[display_idx]["text"]
                ):
                    curr_segment = f"<1><{display_idx}>{commentary_text}"
                # If root display is empty, dont add any mapping
                else:
                    curr_segment = commentary_text
            segments.append(curr_segment)
        return segments

    def get_aligned_display_commentary(
        self, root_pecha: Pecha, root_display_pecha: Pecha, commentary_pecha: Pecha
    ) -> List[Dict]:
        root_map = self.get_root_pechas_mapping(root_display_pecha, root_pecha)

        layer_path = next(commentary_pecha.layer_path.rglob("*.json"))
        commentary_anns = self.extract_commentary_anns(
            AnnotationStore(file=str(layer_path))
        )

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
                commentary_texts = None

            elif not root_display_text.strip():
                commentary_texts = None
            else:
                commentary_texts = []
                for m in map:
                    root_idx = m[0]
                    if not root_anns[root_idx]["text"].strip():
                        continue

                    if root_idx - 1 >= len(commentary_anns):
                        continue

                    for ann in commentary_anns:
                        root_indices = parse_root_mapping(ann["root_idx_mapping"])
                        if root_idx in root_indices:
                            commentary_text = ann["text"]
                            if not commentary_text.strip():
                                continue

                            if commentary_text in commentary_texts:
                                continue

                            commentary_texts.append(ann["text"])

            aligned_segments.append(
                {
                    "root_display_text": root_display_text,
                    "commentary_text": commentary_texts,
                }
            )
        return aligned_segments

    def get_serialized_commentary_display(
        self,
        root_pecha: Pecha,
        root_display_pecha: Pecha,
        commentary_pecha: Pecha,
        commentary_display_pecha: Pecha,
    ):
        """
        Input: map from transfer_layer -> display_layer (One to Many)
        Structure in a way such as : <chapter number><display idx>translation text
        Note: From many relation in display layer, take first idx (Sefaria map limitation)
        """
        root_map = self.get_root_pechas_mapping(root_pecha, root_display_pecha)
        commentary_map = self.get_commentary_pechas_mapping(
            commentary_pecha, commentary_display_pecha
        )

        layer_path = next(commentary_display_pecha.layer_path.rglob("*.json"))

        anns = self.extract_anns(AnnotationStore(file=str(layer_path)))

        segments = []
        for idx, ann in anns.items():
            commentary_text = ann["text"]
            root_idx = commentary_map[idx][0][0]
            root_display_idx = root_map[root_idx][0][0]
            segments.append(f"<1><{root_display_idx}>{commentary_text}")

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
                    "root_idx_mapping": ann_metadata["root_idx_mapping"],
                    "text": str(ann),
                }
            )
        return anns

    def map_commentary_layer_to_layer(
        self, src_layer: AnnotationStore, tgt_layer: AnnotationStore
    ):
        """
        1. Extract annotations from source and target layers
        2. Map the annotations from source to target layer
        src_layer -> tgt_layer (One to Many)
        """
        mapping: Dict = {}

        src_anns = self.extract_commentary_anns(src_layer)
        tgt_anns = self.extract_commentary_anns(tgt_layer)

        for src_ann in src_anns:
            src_start, src_end = src_ann["Span"]["start"], src_ann["Span"]["end"]
            src_idx = int(src_ann["root_idx_mapping"])
            mapping[src_idx] = []

            for tgt_ann in tgt_anns:
                tgt_start, tgt_end = tgt_ann["Span"]["start"], tgt_ann["Span"]["end"]
                tgt_indicies = parse_root_mapping(tgt_ann["root_idx_mapping"])
                tgt_idx = tgt_indicies[0]  # Take the first index

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
