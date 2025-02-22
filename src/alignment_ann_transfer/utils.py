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


def map_display_to_transfer_layer(
    display_layer: AnnotationStore, transfer_layer: AnnotationStore
):
    """
    1. Extract annotations from display and transfer layer
    2. Map the annotations from display to transfer layer
    transfer_layer -> display_layer (One to Many)
    """
    map: Dict = {}

    display_anns = extract_anns(display_layer)
    transfer_anns = extract_anns(transfer_layer)

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
