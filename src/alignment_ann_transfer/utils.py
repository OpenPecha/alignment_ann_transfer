from typing import Dict

from stam import AnnotationStore


def extract_anns(layer: AnnotationStore) -> Dict:
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


def map_layer_to_layer(src_layer: AnnotationStore, tgt_layer: AnnotationStore):
    """
    1. Extract annotations from source and target layers
    2. Map the annotations from source to target layer
    tgt_layer -> src_layer (One to Many)
    """
    mapping: Dict = {}

    src_anns = extract_anns(src_layer)
    tgt_anns = extract_anns(tgt_layer)

    for tgt_idx, tgt_span in tgt_anns.items():
        tgt_start, tgt_end = tgt_span["Span"]["start"], tgt_span["Span"]["end"]
        mapping[tgt_idx] = []

        for src_idx, src_span in src_anns.items():
            src_start, src_end = src_span["Span"]["start"], src_span["Span"]["end"]

            # Check for mapping conditions
            if (
                tgt_start
                <= src_start
                < tgt_end  # Source annotation starts within target
                or tgt_start
                < src_end
                <= tgt_end  # Source annotation ends within target
                or (
                    src_start < tgt_start and src_end > tgt_end
                )  # Source fully contains target
            ) and not (
                src_start == tgt_end or src_end == tgt_start
            ):  # No exact edge overlap
                mapping[tgt_idx].append([src_idx, [src_start, src_end]])

    # Sort the mapping by target indices
    return dict(sorted(mapping.items()))
