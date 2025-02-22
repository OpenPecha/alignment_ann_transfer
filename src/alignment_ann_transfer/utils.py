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
    src_layer -> tgt_layer (One to Many)
    """
    mapping: Dict = {}

    src_anns = extract_anns(src_layer)
    tgt_anns = extract_anns(tgt_layer)

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
